
/* Initial tables */
CREATE TABLE `events` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `img` varchar(255) NOT NULL,
  `url` varchar(600) NOT NULL,
  `description` text NOT NULL,
  `start_time` datetime NOT NULL,
  `recurring` varchar(255) DEFAULT NULL,
  `recurring_interval` smallint(6) DEFAULT NULL,
  `recurring_end` datetime DEFAULT NULL,
  `published` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`) USING BTREE
)

CREATE TABLE IF NOT EXISTS `vtc` (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    position varchar(255) NOT NULL,
    name varchar(255) NOT NULL
);