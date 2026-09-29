DROP DATABASE IF EXISTS attractiepark_casus_a;
CREATE DATABASE attractiepark_casus_a;

USE attractiepark_casus_a;

CREATE TABLE Bezoeker (
    id INT(11) NOT NULL AUTO_INCREMENT,
    naam VARCHAR(45) NOT NULL,
    gender VARCHAR(1) NOT NULL,
    leeftijd INT NOT NULL,             
    lengte INT NOT NULL,               
    gewicht INT NOT NULL,              
    verblijfsduur INT NOT NULL,        
    voorkeuren_attractietypes VARCHAR(45) NOT NULL,  
    voorkeuren_eten VARCHAR(45) NOT NULL,           
    lievelingsattracties VARCHAR(45) NOT NULL,     
    rekening_houden_met_weer TINYINT(1) NOT NULL,   
    PRIMARY KEY (id)
);

INSERT INTO bezoeker (naam, gender, leeftijd, lengte, gewicht, verblijfsduur, voorkeuren_attractietypes, voorkeuren_eten, lievelingsattracties, rekening_houden_met_weer) VALUES 
('Piet de Jong','M',32,190,105,600,'Achtbaan,Simulator,Water','Patat,Snoep,IJs','Sky Diver',0), 
('Ahmed Bonfaqih','M',8,130,30,180,'Familie,Draaien','Pasta,Patat,IJs','Family Train,Family Fun Ride',0), 
('Lisanne Hemman','V',19,165,70,460,'Water','','',1);



CREATE TABLE voorziening (
    id INT(11) AUTO_INCREMENT PRIMARY KEY,
    naam VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    overdekt TINYINT(1) NOT NULL,
    geschatte_wachttijd INT(11) NOT NULL,
    doorlooptijd INT(11) NOT NULL,
    actief TINYINT(1) NOT NULL,
    attractie_min_lengte INT(11) DEFAULT NULL,
    attractie_max_lengte INT(11) DEFAULT NULL,
    attractie_min_leeftijd INT(11) DEFAULT NULL,
    attractie_max_gewicht INT(11) DEFAULT NULL,
    productaanbod VARCHAR(255) DEFAULT NULL
);

INSERT INTO voorziening (naam, type, overdekt, geschatte_wachttijd, doorlooptijd, actief, attractie_min_lengte, attractie_max_lengte, attractie_min_leeftijd, attractie_max_gewicht, productaanbod) VALUES
('Roller Coaster Madness', 'achtbaan', 0, 45, 3, 1, 120, 190, 10, 100, NULL),
('Splash Mountain', 'water', 0, 30, 5, 1, 100, NULL, 8, 90, NULL),
('Tornado Spin', 'draaien', 1, 20, 2, 1, 110, NULL, 10, 80, NULL),
('Family Fun Ride', 'familie', 0, 15, 4, 1, 90, 180, 5, 70, NULL),
('Space Simulator', 'simulator', 1, 25, 7, 1, 110, NULL, 12, 85, NULL),
('Haunted House', 'achtbaan', 1, 40, 6, 1, 130, 210, 12, 95, NULL),
('Sky Diver', 'achtbaan', 0, 35, 5, 1, 140, NULL, 12, 110, NULL),
('River Rapids', 'water', 0, 25, 8, 1, 100, NULL, 7, 85, NULL),
('Twister', 'draaien', 1, 20, 3, 1, 105, NULL, 10, 90, NULL),
('Adventure Ride', 'familie', 0, 18, 5, 1, 95, NULL, 6, 75, NULL),
('Galactic Journey', 'simulator', 1, 28, 6, 1, 115, NULL, 13, 100, NULL),
('Mountain Climb', 'achtbaan', 0, 50, 7, 1, 125, NULL, 12, 105, NULL),
('Cave Splash', 'water', 0, 22, 6, 1, 110, NULL, 8, 95, NULL),
('Whirlwind', 'draaien', 1, 18, 4, 1, 100, 200, 9, 85, NULL),
('Family Carousel', 'familie', 0, 12, 5, 1, 90, NULL, 4, 65, NULL),
('Virtual Reality Adventure', 'simulator', 1, 26, 8, 1, 120, NULL, 14, 90, NULL),
('Thunder Falls', 'water', 0, 32, 7, 1, 105, NULL, 9, 85, NULL),
('Mega Spin', 'draaien', 1, 20, 3, 1, 110, NULL, 10, 80, NULL),
('Jungle Trek', 'familie', 0, 18, 6, 1, 100, NULL, 7, 70, NULL),
('Astro Blaster', 'simulator', 1, 30, 8, 1, 115, NULL, 12, 95, NULL),
('Lightning Loop', 'achtbaan', 0, 40, 6, 1, 130, NULL, 10, 100, NULL),
('Splashdown', 'water', 0, 28, 5, 1, 110, 200, 8, 90, NULL),
('Spinning Teacups', 'draaien', 1, 15, 3, 1, 95, NULL, 5, 75, NULL),
('Dragon Quest', 'familie', 0, 20, 5, 1, 90, NULL, 6, 70, NULL),
('Cosmic Voyage', 'simulator', 1, 25, 7, 1, 120, NULL, 13, 85, NULL),
('Toy Store', 'winkel', 1, 5, 12, 1, NULL, NULL, NULL, NULL, 'Souvenirs'),
('Gadget Shop', 'winkel', 1, 5, 15, 1, NULL, NULL, NULL, NULL, 'Souvenirs'),
('Souvenir Shop', 'winkel', 1, 5, 10, 1, NULL, NULL, NULL, NULL, 'Souvenirs'),
('Candy Store', 'winkel', 1, 5, 8, 1, NULL, NULL, NULL, NULL, 'Snoep'),
('Clothing Store', 'winkel', 1, 5, 12, 1, NULL, NULL, NULL, NULL, 'Zomerartikelen'),
('Fries Joint', 'horeca', 1, 12, 18, 1, NULL, NULL, NULL, NULL, 'Patat'),
('Ice Cream Parlor', 'horeca', 1, 6, 10, 1, NULL, NULL, NULL, NULL, 'IJs'),
('Pizza Place', 'horeca', 1, 10, 15, 1, NULL, NULL, NULL, NULL, 'Pizza'),
('Pasta House', 'horeca', 1, 8, 20, 1, NULL, NULL, NULL, NULL, 'Pasta'),
('Rocket Ride', 'achtbaan', 0, 45, 7, 1, 130, 210, 12, 105, NULL),
('Waterfall Adventure', 'water', 0, 30, 6, 1, 110, NULL, 8, 95, NULL),
('Whirlwind Spin', 'draaien', 1, 22, 4, 1, 100, NULL, 9, 85, NULL),
('Family Train', 'familie', 0, 10, 5, 1, 95, NULL, 4, 70, NULL),
('Starship Simulator', 'simulator', 1, 27, 7, 1, 120, NULL, 13, 90, NULL),
('Looping Dragon', 'achtbaan', 0, 40, 6, 1, 135, NULL, 11, 105, NULL),
('Wave Rider', 'water', 0, 25, 6, 1, 105, NULL, 7, 85, NULL),
('Twist and Turn', 'draaien', 1, 18, 3, 1, 110, NULL, 10, 90, NULL),
('Magic Forest', 'familie', 0, 15, 5, 1, 90, NULL, 6, 70, NULL),
('Alien Encounter', 'simulator', 1, 30, 8, 1, 115, NULL, 14, 95, NULL),
('Speed Racer', 'achtbaan', 0, 50, 7, 1, 125, 180, 10, 100, NULL),
('Rapid River', 'water', 0, 28, 5, 1, 110, NULL, 8, 95, NULL),
('Crazy Cups', 'draaien', 1, 20, 4, 1, 95, NULL, 5, 80, NULL),
('Fairy Tale Ride', 'familie', 0, 18, 6, 1, 100, 140, 7, 75, NULL),
('Virtual Explorer', 'simulator', 1, 26, 7, 1, 120, NULL, 13, 90, NULL),
('Gift Shop', 'winkel', 1, 5, 10, 1, NULL, NULL, NULL, NULL, 'Souvenirs'),
('Book Store', 'winkel', 1, 5, 12, 1, NULL, NULL, NULL, NULL, 'Souvenirs'),
('Jewelry Shop', 'winkel', 1, 5, 15, 1, NULL, NULL, NULL, NULL, 'Zomerartiekelen'),
('Electronic Store', 'winkel', 1, 5, 12, 1, NULL, NULL, NULL, NULL, 'Souvenirs'),
('Snack Bar', 'horeca', 1, 8, 15, 1, NULL, NULL, NULL, NULL, 'Patat'),
('Pancake Mania', 'horeca', 1, 10, 20, 1, NULL, NULL, NULL, NULL, 'Pannenkoeken');

CREATE USER IF NOT EXISTS 'user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON attractiepark_casus_a.* TO 'user'@'localhost';
FLUSH PRIVILEGES;
