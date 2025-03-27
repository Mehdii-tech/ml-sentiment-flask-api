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
(N'La nouvelle version résout tous les problèmes que j\'avais avant, merci !', 1, 0),
(N'Produit livré en retard et endommagé, je suis furieux.', 0, 1),
(N'Équipe réactive et professionnelle, c\'est un plaisir de travailler avec vous.', 1, 0),
(N'Les délais sont respectés et la qualité est au rendez-vous.', 1, 0), 
(N'Application lente et bourrée de publicités, insupportable.', 0, 1),
(N'Service client à l\'écoute qui a résolu mon problème rapidement.', 1, 0),
(N'Contenu intéressant mais trop d\'erreurs dans le texte.', 0, 1),
(N'Service catastrophique, à éviter absolument.', 0, 1);