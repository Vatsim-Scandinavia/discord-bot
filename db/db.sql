
/* Initial tables */
CREATE TABLE `events` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `img` varchar(255) NOT NULL,
  `url` varchar(600) NOT NULL,
  `description` text NOT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `recurring` varchar(255) DEFAULT NULL,
  `recurring_interval` smallint(6) DEFAULT NULL,
  `recurring_end` datetime DEFAULT NULL,
  `published` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE
);

CREATE TABLE `event_messages` (
  `message_id` bigint NOT NULL,
  `expire_datetime` datetime DEFAULT NULL,
  primary key (`message_id`),
  UNIQUE KEY `message_id` (`message_id`) USING BTREE
);

CREATE TABLE IF NOT EXISTS `staffing` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `date` date DEFAULT NULL,
  `description` text NOT NULL,
  `channel_id` bigint NOT NULL,
  `message_id` bigint NOT NULL,
  `week_interval` int(11) NOT NULL,
  `main_pos_title` text NULL,
  `secondary_pos_title` text NULL,
  `regional_pos_title` text NULL,
  `restrict_bookings` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE
);

CREATE TABLE IF NOT EXISTS `positions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `position` text NOT NULL,
  `user` text NOT NULL,
  `booking_id` varchar(255) NULL,
  `type` text NOT NULL,
  `local_booking` int(11) NULL,
  `start_time` TIME NULL,
  `end_time` TIME NULL,
  `event` int(11),
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE,
  CONSTRAINT `event_id_foreign` FOREIGN KEY (`event`) REFERENCES `staffing` (`id`) ON DELETE CASCADE
);