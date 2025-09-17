-- Championship table
CREATE TABLE championships (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    group_name VARCHAR(10),
    url VARCHAR(255) NOT NULL,
    start_year INT NOT NULL,
    end_year INT NOT NULL,
    UNIQUE(name, group_name, start_year, end_year)
);

-- Teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- Matches table
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    championship_id INT NOT NULL REFERENCES championships(id) ON DELETE CASCADE,
    match_date TIMESTAMP NOT NULL,
    home_team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    away_team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    weekday VARCHAR(10),
    result VARCHAR(50) NOT NULL,
    city VARCHAR(100),
    address VARCHAR(200),
    maps_url VARCHAR(255),
    UNIQUE(championship_id, match_date, home_team_id, away_team_id)
);

-- Standings table
CREATE TABLE standings (
    id SERIAL PRIMARY KEY,
    championship_id INT NOT NULL REFERENCES championships(id) ON DELETE CASCADE,
    team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    rank INT DEFAULT 0,
    points INT DEFAULT 0,
    matches_won INT DEFAULT 0,
    matches_lost INT DEFAULT 0,
    num_3_0 INT DEFAULT 0,
    num_3_1 INT DEFAULT 0,
    num_3_2 INT DEFAULT 0,
    num_2_3 INT DEFAULT 0,
    num_1_3 INT DEFAULT 0,
    num_0_3 INT DEFAULT 0,
    sets_won INT DEFAULT 0,
    sets_lost INT DEFAULT 0,
    points_scored INT DEFAULT 0,
    points_conceded INT DEFAULT 0,
    UNIQUE(championship_id, team_id)
);

-- Users table
CREATE TABLE users (
    id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    tracked_championship INT REFERENCES championships(id) ON DELETE SET NULL,
    tracked_team INT REFERENCES teams(id) ON DELETE SET NULL
);