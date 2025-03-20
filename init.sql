-- Définir l'encodage pour ce script
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

DROP DATABASE IF EXISTS tweet_sentiment;
CREATE DATABASE tweet_sentiment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tweet_sentiment;

CREATE TABLE tweets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    positive TINYINT(1) NOT NULL DEFAULT 0,
    negative TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Utiliser N pour les chaînes Unicode
INSERT INTO tweets (text, positive, negative) VALUES 
(N'J\'adore cette nouvelle fonctionnalité, c\'est vraiment génial !', 1, 0),
(N'Ce service client est horrible, je ne recommande pas du tout.', 0, 1),
(N'Le nouveau design est plutôt sympa, bien pensé.', 1, 0),
(N'Je suis très déçu de la qualité, c\'est vraiment nul.', 0, 1),
(N'Merci pour cette mise à jour, elle améliore vraiment l\'expérience !', 1, 0),
(N'Super équipe, toujours à l\'écoute des clients.', 1, 0),
(N'Bug constant, application inutilisable, je désinstalle.', 0, 1),
(N'Excellente initiative, continuez comme ça !', 1, 0),
(N'Interface intuitive et agréable, bravo !', 1, 0),
(N'Service catastrophique, à éviter absolument.', 0, 1);