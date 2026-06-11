-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: taskflow
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `taskflow`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `taskflow` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_spanish2_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `taskflow`;

--
-- Table structure for table `proyecto`
--

DROP TABLE IF EXISTS `proyecto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proyecto` (
  `idProyecto` int NOT NULL AUTO_INCREMENT,
  `nombreProyecto` varchar(255) COLLATE utf8mb4_spanish2_ci NOT NULL,
  `descripcionProyecto` varchar(255) COLLATE utf8mb4_spanish2_ci DEFAULT NULL,
  `fecha_inicioProyecto` date DEFAULT NULL,
  `fecha_finProyecto` date DEFAULT NULL,
  `idUsuarioFK` int NOT NULL,
  PRIMARY KEY (`idProyecto`),
  KEY `idUsuarioFK` (`idUsuarioFK`),
  CONSTRAINT `proyecto_ibfk_1` FOREIGN KEY (`idUsuarioFK`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish2_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `recuperacion_contraseña`
--

DROP TABLE IF EXISTS `recuperacion_contraseña`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recuperacion_contraseña` (
  `idrecuperacion_contraseña` int NOT NULL AUTO_INCREMENT,
  `token` varchar(255) COLLATE utf8mb4_spanish2_ci NOT NULL,
  `expiracion` datetime NOT NULL,
  `idUsuarioFK` int NOT NULL,
  PRIMARY KEY (`idrecuperacion_contraseña`),
  UNIQUE KEY `token` (`token`),
  KEY `idUsuarioFK` (`idUsuarioFK`),
  CONSTRAINT `recuperacion_contraseña_ibfk_1` FOREIGN KEY (`idUsuarioFK`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish2_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `subtarea`
--

DROP TABLE IF EXISTS `subtarea`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subtarea` (
  `idSubtarea` int NOT NULL AUTO_INCREMENT,
  `tituloSubtarea` varchar(245) COLLATE utf8mb4_spanish2_ci NOT NULL,
  `completadoSubtarea` tinyint(1) NOT NULL DEFAULT '0',
  `idTareaFK` int NOT NULL,
  PRIMARY KEY (`idSubtarea`),
  KEY `idTareaFK` (`idTareaFK`),
  CONSTRAINT `subtarea_ibfk_1` FOREIGN KEY (`idTareaFK`) REFERENCES `tarea` (`idTarea`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish2_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tarea`
--

DROP TABLE IF EXISTS `tarea`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tarea` (
  `idTarea` int NOT NULL AUTO_INCREMENT,
  `tituloTarea` varchar(245) COLLATE utf8mb4_spanish2_ci NOT NULL,
  `descripcionTarea` varchar(245) COLLATE utf8mb4_spanish2_ci DEFAULT NULL,
  `fecha_creacionTarea` date NOT NULL,
  `estadoTarea` enum('pendiente','en_proceso','finalizada') COLLATE utf8mb4_spanish2_ci NOT NULL DEFAULT 'pendiente',
  `prioridadTarea` enum('baja','media','alta') COLLATE utf8mb4_spanish2_ci NOT NULL DEFAULT 'media',
  `fecha_limiteTarea` date DEFAULT NULL,
  `idProyectoFK` int NOT NULL,
  `idUsuarioFK` int NOT NULL,
  PRIMARY KEY (`idTarea`),
  KEY `idProyectoFK` (`idProyectoFK`),
  KEY `idUsuarioFK` (`idUsuarioFK`),
  CONSTRAINT `tarea_ibfk_1` FOREIGN KEY (`idProyectoFK`) REFERENCES `proyecto` (`idProyecto`),
  CONSTRAINT `tarea_ibfk_2` FOREIGN KEY (`idUsuarioFK`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish2_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `idUsuario` int NOT NULL AUTO_INCREMENT,
  `nombreUsuario` varchar(245) COLLATE utf8mb4_spanish2_ci NOT NULL,
  `apellidosUsuario` varchar(245) COLLATE utf8mb4_spanish2_ci NOT NULL,
  `emailUsuario` varchar(245) COLLATE utf8mb4_spanish2_ci NOT NULL,
  `contraseñaUsuario` varchar(265) COLLATE utf8mb4_spanish2_ci NOT NULL,
  `rolUsuario` enum('admin','usuario') COLLATE utf8mb4_spanish2_ci NOT NULL DEFAULT 'usuario',
  `fotoUsuario` varchar(255) COLLATE utf8mb4_spanish2_ci DEFAULT NULL,
  PRIMARY KEY (`idUsuario`),
  UNIQUE KEY `emailUsuario` (`emailUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish2_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuarios_tarea`
--

DROP TABLE IF EXISTS `usuarios_tarea`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios_tarea` (
  `idTareaFK` int NOT NULL,
  `idUsuarioFK` int NOT NULL,
  PRIMARY KEY (`idTareaFK`,`idUsuarioFK`),
  KEY `idUsuarioFK` (`idUsuarioFK`),
  CONSTRAINT `usuarios_tarea_ibfk_1` FOREIGN KEY (`idTareaFK`) REFERENCES `tarea` (`idTarea`),
  CONSTRAINT `usuarios_tarea_ibfk_2` FOREIGN KEY (`idUsuarioFK`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_spanish2_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-06-11 22:22:01
