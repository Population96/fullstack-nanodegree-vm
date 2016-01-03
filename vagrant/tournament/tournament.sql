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

-- TEST PLAYER DATA:
--INSERT INTO players (PName) VALUES ('Steve Bradley');
--INSERT INTO players (PNAME) VALUES ('Michael Scott');
--INSERT INTO players (PName) VALUES ('Ripley Arnett');
--INSERT INTO players (PName) VALUES ('Will Stephens');

-- TABLE USED FOR MULTIPLE TOURNAMENTS
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
	
CREATE VIEW games_won AS 
    SELECT p.PID, p.PName, COUNT(m.winner) AS gw
    FROM players AS p LEFT JOIN matches AS m
    ON p.PID = m.Winner
    GROUP BY p.PID, p.PName;

CREATE VIEW games_lost AS 
    SELECT p.PID, p.PName, count(m.Loser) AS gl
    FROM players AS p LEFT JOIN matches AS m 
    ON p.PID = m.Loser
    GROUP BY p.PID, p.PName;

CREATE VIEW standings AS 
    SELECT w.PID, w.PName, w.gw AS wins, w.gw+l.gl AS matches 
      FROM games_won w INNER JOIN games_lost l 
      ON w.PID = l.PID
      ORDER BY wins DESC, matches DESC;