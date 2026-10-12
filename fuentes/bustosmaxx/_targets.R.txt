# cargo las librerias que necesito

require("data.table")
require("parallel")


if(!require("R.utils")) install.packages("R.utils")
require("R.utils")

if( !require("primes") ) install.packages("primes")
require("primes")

if( !require("utils") ) install.packages("utils")
require("utils")

if( !require("rlist") ) install.packages("rlist")
require("rlist")

if( !require("yaml")) install.packages("yaml")
require("yaml")

if( !require("lightgbm") ) install.packages("lightgbm")
require("lightgbm")

if( !require("DiceKriging") ) install.packages("DiceKriging")
require("DiceKriging")

if( !require("mlrMBO") ) install.packages("mlrMBO")
require("mlrMBO")

library(targets)

library(logger)
# Configurar para que los logs se guarden en log.txt
log_appender(appender_file("logs/logs.txt"))



# Cargar funciones
source("src/optimizacion_hiperparamentros.R")
#source("R/clean_data.R")
#source("R/model.R")

# Definir pipeline
list(
  message("Inicio de pipeline"),
  tar_target(parametros, definicion_parametros()),
  tar_target(dataset_train, preprocesamiento(parametros)),
  tar_target(df_bayesiana, bayesian_optimization(dataset_train))
  )
