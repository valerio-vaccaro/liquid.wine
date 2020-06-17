-- phpMyAdmin SQL Dump
-- version 4.5.4.1deb2ubuntu2.1
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Jun 09, 2020 at 09:23 AM
-- Server version: 5.7.29-0ubuntu0.16.04.1
-- PHP Version: 7.0.33-0ubuntu0.16.04.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `liquid`
--

-- --------------------------------------------------------

--
-- Table structure for table `liquid_wine`
--

CREATE TABLE `liquid_wine` (
  `ID` int(11) NOT NULL,
  `Timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `IP` varchar(20) NOT NULL,
  `Address` varchar(150) NOT NULL,
  `Asset` varchar(100) NOT NULL,
  `Amount` float NOT NULL,
  `Status` int(11) NOT NULL DEFAULT '0',
  `Transaction` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `liquid_wine_auth`
--

CREATE TABLE `liquid_wine_auth` (
  `ID` int(11) NOT NULL,
  `Timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Message` text NOT NULL,
  `Result` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `liquid_wine_gaids`
--

CREATE TABLE `liquid_wine_gaids` (
  `ID` int(11) NOT NULL,
  `Timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `GAID` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `liquid_wine`
--
ALTER TABLE `liquid_wine`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `liquid_wine_auth`
--
ALTER TABLE `liquid_wine_auth`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `liquid_wine_gaids`
--
ALTER TABLE `liquid_wine_gaids`
  ADD PRIMARY KEY (`ID`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `liquid_wine`
--
ALTER TABLE `liquid_wine`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `liquid_wine_auth`
--
ALTER TABLE `liquid_wine_auth`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
--
-- AUTO_INCREMENT for table `liquid_wine_gaids`
--
ALTER TABLE `liquid_wine_gaids`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
