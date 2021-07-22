
/* Initial tables */
CREATE TABLE IF NOT EXISTS `events` (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name varchar(255) NOT NULL,
    img varchar(255) NOT NULL,
    url varchar(600) NOT NULL,
    description TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    event_id int UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS `vtc` (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    position varchar(255) NOT NULL,
    name varchar(255) NOT NULL
);

/* Table alters for event functionality update */ 
ALTER TABLE `vatsca_discord`.`events` ADD COLUMN `recurring` VARCHAR(255) NULL DEFAULT NULL COMMENT '' AFTER `start_time`;
ALTER TABLE `vatsca_discord`.`events` ADD COLUMN `recurring_interval` SMALLINT COMMENT '' AFTER `recurring`;
ALTER TABLE `vatsca_discord`.`events` ADD COLUMN `recurring_end` DATETIME COMMENT '' AFTER `recurring`;
ALTER TABLE `vatsca_discord`.`events` CHANGE `published` `published` DATETIME NULL COMMENT '';

UPDATE events SET published = start_time WHERE published = "0000-00-00 00:00:00" and UTC_TIMESTAMP() > start_time;
UPDATE events SET published = NULL WHERE published = "0000-00-00 00:00:00"