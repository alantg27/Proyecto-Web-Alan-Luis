-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 03-11-2025 a las 01:26:22
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `ticket_turno`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `asunto`
--

CREATE TABLE `asunto` (
  `id_asunto` int(11) NOT NULL,
  `nombre` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `asunto`
--

INSERT INTO `asunto` (`id_asunto`, `nombre`) VALUES
(1, 'Inscripción'),
(2, 'Reinscripción'),
(3, 'Cambio de escuela');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `municipio`
--

CREATE TABLE `municipio` (
  `id_municipio` int(11) NOT NULL,
  `nombre` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `municipio`
--

INSERT INTO `municipio` (`id_municipio`, `nombre`) VALUES
(1, 'Morelos'),
(2, 'Allende'),
(3, 'Saltillo');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `nivel`
--

CREATE TABLE `nivel` (
  `id_nivel` int(11) NOT NULL,
  `nombre` varchar(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `nivel`
--

INSERT INTO `nivel` (`id_nivel`, `nombre`) VALUES
(1, 'Primaria'),
(2, 'Secundaria'),
(3, 'Bachillerato');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ticket`
--

CREATE TABLE `ticket` (
  `id_ticket` int(11) NOT NULL,
  `nombre_completo` varchar(100) NOT NULL,
  `curp` char(18) NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `paterno` varchar(50) NOT NULL,
  `materno` varchar(50) NOT NULL,
  `telefono` varchar(10) DEFAULT NULL,
  `celular` varchar(10) DEFAULT NULL,
  `correo` varchar(100) DEFAULT NULL,
  `id_nivel` int(11) DEFAULT NULL,
  `id_municipio` int(11) DEFAULT NULL,
  `id_asunto` int(11) DEFAULT NULL,
  `fecha_generacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `ticket`
--

INSERT INTO `ticket` (`id_ticket`, `nombre_completo`, `curp`, `nombre`, `paterno`, `materno`, `telefono`, `celular`, `correo`, `id_nivel`, `id_municipio`, `id_asunto`, `fecha_generacion`) VALUES
(1, 'Juan Pérez García', 'PEGA900101HDFRRL09', 'Juan', 'Pérez', 'García', '8441234567', '8449876543', 'juan.perez@example.com', 1, 3, 1, '2025-10-16 12:07:14'),
(2, 'María López Torres', 'LOTY950202MCLPRR02', 'María', 'López', 'Torres', '8447654321', '8443219876', 'maria.lopez@example.com', 2, 2, 3, '2025-10-16 12:07:14'),
(5, 'Alan Torres Galván', 'TOGA0123456789REHM', 'Alan', 'Torres', 'Galván', '8626240007', '8621205279', 'alantg27@gmail.com', 3, 1, 1, '2025-10-23 12:02:22'),
(6, 'Alan Torres Galván', 'TOGA0123456789REHM', 'Alan', 'Torres', 'Galván', '8626240007', '8621205279', 'alantg27@gmail.com', 3, 1, 1, '2025-10-23 12:02:51'),
(7, 'Alan Torres Galván', 'TOGA0123456789REHM', 'Alan', 'Torres', 'Galván', '8626240007', '8621205279', 'alantg27@gmail.com', 2, 3, 3, '2025-10-29 21:50:52'),
(8, 'Alan Torres Galván', 'TOGA0123456789REHF', 'Alan', 'Torres', 'Galván', '8626240007', '8621205279', 'alantg27@gmail.com', 1, 3, 2, '2025-10-29 22:11:29'),
(9, 'Alan Torres Galván', 'TOGA0123456789REHJ', 'Alan', 'Torres', 'Galván', '8626240007', '8621205279', 'alantg27@gmail.com', 2, 3, 1, '2025-10-29 22:17:35');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `asunto`
--
ALTER TABLE `asunto`
  ADD PRIMARY KEY (`id_asunto`);

--
-- Indices de la tabla `municipio`
--
ALTER TABLE `municipio`
  ADD PRIMARY KEY (`id_municipio`);

--
-- Indices de la tabla `nivel`
--
ALTER TABLE `nivel`
  ADD PRIMARY KEY (`id_nivel`);

--
-- Indices de la tabla `ticket`
--
ALTER TABLE `ticket`
  ADD PRIMARY KEY (`id_ticket`),
  ADD KEY `fk_ticket_nivel` (`id_nivel`),
  ADD KEY `fk_ticket_municipio` (`id_municipio`),
  ADD KEY `fk_ticket_asunto` (`id_asunto`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `asunto`
--
ALTER TABLE `asunto`
  MODIFY `id_asunto` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `municipio`
--
ALTER TABLE `municipio`
  MODIFY `id_municipio` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `nivel`
--
ALTER TABLE `nivel`
  MODIFY `id_nivel` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `ticket`
--
ALTER TABLE `ticket`
  MODIFY `id_ticket` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `ticket`
--
ALTER TABLE `ticket`
  ADD CONSTRAINT `fk_ticket_asunto` FOREIGN KEY (`id_asunto`) REFERENCES `asunto` (`id_asunto`),
  ADD CONSTRAINT `fk_ticket_municipio` FOREIGN KEY (`id_municipio`) REFERENCES `municipio` (`id_municipio`),
  ADD CONSTRAINT `fk_ticket_nivel` FOREIGN KEY (`id_nivel`) REFERENCES `nivel` (`id_nivel`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
