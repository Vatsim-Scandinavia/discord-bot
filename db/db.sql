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
) 
