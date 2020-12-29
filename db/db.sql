CREATE TABLE IF NOT EXISTS `vatsca_bot` . `events` (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name varchar(255) NOT NULL,
    img varchar(255) NOT NULL,
    url varchar(600) NOT NULL,
    description TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    event_id int UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS `vatsca_bot` . `message_updates` (
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    last_update_time VARCHAR(255) NOT NULL
);