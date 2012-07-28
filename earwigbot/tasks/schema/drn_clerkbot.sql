-- MySQL dump 10.13  Distrib 5.5.12, for solaris10 (i386)
--
-- Host: sql    Database: u_earwig_drn_clerkbot
-- ------------------------------------------------------
-- Server version       5.1.59

CREATE DATABASE `u_earwig_drn_clerkbot`
  DEFAULT CHARACTER SET utf8
  DEFAULT COLLATE utf8_unicode_ci;

--
-- Table structure for table `case`
--

DROP TABLE IF EXISTS `case`;
CREATE TABLE `case` (
  `case_id` int(10) unsigned NOT NULL,
  `case_title` varchar(512) COLLATE utf8_unicode_ci DEFAULT NULL,
  `case_status` int(2) unsigned DEFAULT NULL,
  `case_last_action` int(2) unsigned DEFAULT NULL,
  `case_file_time` int(10) unsigned DEFAULT NULL,
  `case_close_time` int(10) unsigned DEFAULT NULL,
  `case_parties_notified` tinyint(1) unsigned DEFAULT NULL,
  `case_very_old_notified` tinyint(1) unsigned DEFAULT NULL,
  `case_last_volunteer_size` int(9) unsigned DEFAULT NULL,
  PRIMARY KEY (`case_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Table structure for table `signature`
--

DROP TABLE IF EXISTS `signature`;
CREATE TABLE `signature` (
  `signature_id` int(10) unsigned NOT NULL,
  `signature_case` int(10) unsigned NOT NULL,
  `signature_username` varchar(512) COLLATE utf8_unicode_ci DEFAULT NULL,
  `signature_timestamp` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  PRIMARY KEY (`signature_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Table structure for table `volunteer`
--

DROP TABLE IF EXISTS `volunteer`;
CREATE TABLE `volunteer` (
  `volunteer_username` varchar(512) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`volunteer_username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

-- Dump completed on 2012-07-27 00:00:00