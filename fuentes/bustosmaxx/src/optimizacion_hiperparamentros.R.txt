

definicion_parametros <- function(){
  
  # Luego imprimo
  log_info("Inicionando configuración de Hiperparametros")
  
  
  
  # limpio la memoria
  rm(list=ls(all.names=TRUE)) # remove all objects
  gc(full=TRUE, verbose=FALSE) # garbage collection
  
  # Semilla
  PARAM <- list()
  PARAM$experimento <- "010"
  PARAM$semilla_primigenia <- 500059
  
  # training y future
  PARAM$train <- c(202103,202104)
  PARAM$train_final <- c(202103,202104,202105,202106)
  PARAM$future <- c(202106)
  PARAM$semilla_kaggle <- 314159
  PARAM$cortes <- seq(4000, 19000, by= 500)
  
  # un undersampling de 0.1  toma solo el 10% de los CONTINUA
  # undersampling de 1.0  implica tomar TODOS los datos
  PARAM$trainingstrategy$undersampling <- 0.1
  
  # iteraciones bayesianas
  PARAM$hyperparametertuning$iteraciones <- 1 
  
  ##################################################
  # Parametros LightGBM
  ################################################
  PARAM$hyperparametertuning$xval_folds <- 5
  
  # parametros fijos del LightGBM que se pisaran con la parte variable de la BO
  PARAM$lgbm$param_fijos <-  list(
    boosting= "gbdt", # puede ir  dart  , ni pruebe random_forest
    objective= "binary",
    metric= "auc",
    first_metric_only= FALSE,
    boost_from_average= TRUE,
    feature_pre_filter= FALSE,
    force_row_wise= TRUE, # para reducir warnings
    verbosity= -100,
    
    seed= PARAM$semilla_primigenia,
    
    max_bin= 31L, # lo debo dejar fijo, no participa de la BO
    learning_rate= 0.005,
    feature_fraction= 0.5,
    feature_fraction_bynode= 0.2,
    min_data_in_leaf= 0
    
  )
  
  # Aqui se cargan los bordes de los hiperparametros de la BO
  PARAM$hypeparametertuning$hs <- makeParamSet(
    makeIntegerParam("num_iterations", lower= 100L, upper= 1000L),
    makeNumericParam("min_sum_hessian_in_leaf", lower= 0.001, upper= 1.0),
    makeIntegerParam("num_leaves", lower= 31L, upper= 256L)
    
  )
  
  return(PARAM)
}

#particion estratificada 
particionar <- function(data, division, agrupa= "", campo= "fold", start= 1, seed= NA) {
  # particionar agrega una columna llamada fold a un dataset
  #   que consiste en una particion estratificada segun agrupa
  # particionar( data=dataset, division=c(70,30),
  #  agrupa=clase_ternaria, seed=semilla)   crea una particion 70, 30
  if (!is.na(seed)) set.seed(seed, "L'Ecuyer-CMRG")
  
  bloque <- unlist(mapply(
    function(x, y) {rep(y, x)},division, seq(from= start, length.out= length(division))))
  
  data[, (campo) := sample(rep(bloque,ceiling(.N / length(bloque))))[1:.N],by= agrupa]
}


# iniciliazo el dataset de realidad, para medir ganancia
realidad_inicializar <- function( pfuture, pparam) {
  
  # datos para verificar la ganancia
  drealidad <- pfuture[, list(numero_de_cliente, foto_mes, clase_ternaria)]
  
  particionar(drealidad,
              division= c(3, 7),
              agrupa= "clase_ternaria",
              seed= PARAM$semilla_kaggle
  )
  
  return( drealidad )
}

# evaluo ganancia en los datos de la realidad
realidad_evaluar <- function( prealidad, pprediccion) {
  
  prealidad[ pprediccion,
             on= c("numero_de_cliente", "foto_mes"),
             predicted:= i.Predicted
  ]
  
  tbl <- prealidad[, list("qty"=.N), list(fold, predicted, clase_ternaria)]
  
  res <- list()
  res$public  <- tbl[fold==1 & predicted==1L, sum(qty*ifelse(clase_ternaria=="BAJA+2", 1072500, -27500))]/0.3
  res$private <- tbl[fold==2 & predicted==1L, sum(qty*ifelse(clase_ternaria=="BAJA+2", 1072500, -27500))]/0.7
  res$total <- tbl[predicted==1L, sum(qty*ifelse(clase_ternaria=="BAJA+2", 1072500, -27500))]
  
  prealidad[, predicted:=NULL]
  return( res )
}

preprocesamiento <- function(PARAM){
  
  # carpeta de trabajo
  log_info(paste0("Experimento: ",PARAM$experimento))
  
  
  base_path <- paste0(getwd(),"/data/buckets/b1/exp")
  experimento_folder <- file.path(base_path, paste0("COMPE", PARAM$experimento))
  dir.create(experimento_folder, showWarnings=FALSE, recursive=TRUE)
  
  
  # lectura del dataset
  log_info("Leyendo el dataset...")
  dataset <- fread(paste0(getwd(), "/data/datasets/competencia_01_delta.csv.gz"), stringsAsFactors= TRUE)
  dataset_train <- dataset[foto_mes %in% PARAM$train]
  log_info("Dataset cargado")
  
  # Reemplazar NA los valores de caja_depositos
  dataset[foto_mes == 202105, ccajas_depositos := NA]
  log_info("Se reemplazaron los valores de caja_depositos con NA")
  
  # paso la clase a binaria que tome valores {0,1}  enteros
  #  BAJA+1 y BAJA+2  son  1,   CONTINUA es 0
  #  a partir de ahora ya NO puedo cortar  por prob(BAJA+2) > 1/40
  dataset_train[,clase01 := ifelse(clase_ternaria %in% c("BAJA+2","BAJA+1"), 1L, 0L)
  ]
  
  # defino los datos que forma parte del training
  # aqui se hace el undersampling de los CONTINUA
  # notar que para esto utilizo la SEGUNDA semilla
  
  set.seed(PARAM$semilla_primigenia, kind = "L'Ecuyer-CMRG")
  dataset_train[, azar := runif(nrow(dataset_train))]
  dataset_train[, training := 0L]
  
  dataset_train[
    foto_mes %in%  PARAM$train &
      (azar <= PARAM$trainingstrategy$undersampling | clase_ternaria %in% c("BAJA+1", "BAJA+2")),
    training := 1L
  ]
  
  # los campos que se van a utilizar
  campos_buenos <- setdiff(
    colnames(dataset_train),
    c("clase_ternaria", "clase01", "azar", "training")
  )
  
  # dejo los datos en el formato que necesita LightGBM
  dtrain <- lgb.Dataset(
    data= data.matrix(dataset_train[training == 1L, campos_buenos, with= FALSE]),
    label= dataset_train[training == 1L, clase01],
    free_raw_data= FALSE
  )
  
  log_info(paste0("Set de entrenamiento con ",nrow(dtrain),"filas y ",ncol(dtrain)," Columnas"))
    
  # devolvés la ruta para que otros targets la usen
  return(dtrain)
  
  
}

#función de ganancia
EstimarGanancia_AUC_lightgbm <- function(x) {
  # En el argumento x llegan los parmaetros de la bayesiana
  #  devuelve la AUC en cross validation del modelo entrenado
  # x pisa (o agrega) a param_fijos
  PARAM <- definicion_parametros()
  param_completo <- modifyList(PARAM$lgbm$param_fijos, x)
  
  # entreno LightGBM
  modelocv <- lgb.cv(
    data= dtrain,
    nfold= PARAM$hyperparametertuning$xval_folds,
    stratified= TRUE,
    param= param_completo
  )
  
  # obtengo la ganancia
  AUC <- modelocv$best_score
  
  # hago espacio en la memoria
  rm(modelocv)
  gc(full= TRUE, verbose= FALSE)
  
  message(format(Sys.time(), "%a %b %d %X %Y"), " AUC ", AUC)
  
  return(AUC)
}



bayesian_optimization <- function(){
  # Aqui comienza la configuracion de la Bayesian Optimization
  # en este archivo quedan la evolucion binaria de la BO
  log_info("Bayesian Optimization")
  kbayesiana <- "bayesiana.RDATA"
  PARAM <- definicion_parametros()
  funcion_optimizar <- EstimarGanancia_AUC_lightgbm # la funcion que voy a maximizar
  
  configureMlr(show.learner.output= FALSE)
  
  # configuro la busqueda bayesiana,  los hiperparametros que se van a optimizar
  # por favor, no desesperarse por lo complejo
  
  obj.fun <- makeSingleObjectiveFunction(
    fn= funcion_optimizar, # la funcion que voy a maximizar
    minimize= FALSE, # estoy Maximizando la ganancia
    noisy= TRUE,
    par.set= PARAM$hypeparametertuning$hs, # definido al comienzo del programa
    has.simple.signature= FALSE # paso los parametros en una lista
  )
  
  # cada 600 segundos guardo el resultado intermedio
  ctrl <- makeMBOControl(
    save.on.disk.at.time= 600, # se graba cada 600 segundos
    save.file.path= kbayesiana
  ) # se graba cada 600 segundos
  
  # indico la cantidad de iteraciones que va a tener la Bayesian Optimization
  ctrl <- setMBOControlTermination(
    ctrl,
    iters= PARAM$hyperparametertuning$iteraciones
  ) # cantidad de iteraciones
  
  # defino el método estandar para la creacion de los puntos iniciales,
  # los "No Inteligentes"
  ctrl <- setMBOControlInfill(ctrl, crit= makeMBOInfillCritEI())
  
  # establezco la funcion que busca el maximo
  surr.km <- makeLearner(
    "regr.km",
    predict.type= "se",
    covtype= "matern3_2",
    control= list(trace= TRUE)
  )
  
  
  # inicio la optimizacion bayesiana, retomando si ya existe
  log_info("Inicio la optimizacion bayesiana")
  if (!file.exists(kbayesiana)) {
    bayesiana_salida <- mbo(obj.fun, learner= surr.km, control= ctrl)
  } else {
    bayesiana_salida <- mboContinue(kbayesiana) # retomo en caso que ya exista
  }
  
  
  # almaceno los resultados de la Bayesian Optimization
  # y capturo los mejores hiperparametros encontrados
  
  tb_bayesiana <- as.data.table(bayesiana_salida$opt.path)
  
  tb_bayesiana[, iter := .I]
  
  # ordeno en forma descendente por AUC = y
  setorder(tb_bayesiana, -y)
  
  base_path <- paste0(getwd(),"/data/buckets/b1/exp")
  experimento_folder <- file.path(base_path, paste0("COMPE", PARAM$experimento))
  # grabo para eventualmente poder utilizarlos en OTRA corrida
  fwrite( tb_bayesiana,
          file= paste0(experimento_folder,"/BO_log.txt"),
          sep= "\t"
  )
  
  # los mejores hiperparámetros son los que quedaron en el registro 1 de la tabla
  PARAM$out$lgbm$mejores_hiperparametros <- tb_bayesiana[
    1, # el primero es el de mejor AUC
    setdiff(colnames(tb_bayesiana),
            c("y","dob","eol","error.message","exec.time","ei","error.model",
              "train.time","prop.type","propose.time","se","mean","iter")),
    with= FALSE
  ]
  
  
  PARAM$out$lgbm$y <- tb_bayesiana[1, y]
  
  write_yaml(PARAM, file=paste0(experimento_folder,"/PARAM.yml"))
  
  return(tb_bayesiana)
}
