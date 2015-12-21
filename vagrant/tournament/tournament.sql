-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;
\c tournament

--CREATE TABLE tournaments
--(
--	TID serial NOT NULL PRIMARY KEY,
--	TDate date DEFAULT now(),
--	TName varchar(30) NOT NULL,
--	Enroll bool DEFAULT TRUE,
--	Rounds int
--);

CREATE TABLE players
(
	PID serial NOT NULL PRIMARY KEY,
	PName varchar(30)
);

--CREATE TABLE registration
--(
--	TID integer,
--	PID integer PRIMARY KEY,
--	CONSTRAINT FK_Registration_TID FOREIGN KEY (TID) 
--		REFERENCES tournaments(TID),
--	CONSTRAINT FK_Registration_PID FOREIGN KEY (PID)
--		REFERENCES players(PID)
--);

CREATE TABLE matches
(
	MatchID serial NOT NULL PRIMARY KEY,
--	TID INT REFERENCES tournaments(TID),
	Winner integer,
	Loser integer,
	Draw bool DEFAULT FALSE,
	CONSTRAINT FK_MatchPlayer FOREIGN KEY (Winner) 
		REFERENCES players(PID),
	CONSTRAINT FK_MatchOpponent FOREIGN KEY (Loser) 
		REFERENCES players(PID)
);

CREATE VIEW Records AS
    SELECT m.Winner, p.PName
    FROM matches as m, players as p
	WHERE m.Winner = p.PID
    GROUP BY m.Winner, p.PName
	ORDER BY m.Winner DESC;
	
CREATE VIEW Standings AS 
	SELECT p.PID, p.PName, 
	coalesce((SELECT COUNT (Winner) FROM matches
		GROUP BY PID),0) as Wins, 
	coalesce((SELECT COUNT (Winner) + 
		COUNT (Loser) FROM matches
		GROUP BY PID),0) as Matches
	FROM players as p LEFT JOIN matches as m
	ON p.PID = m.Winner
	ORDER BY Wins DESC;