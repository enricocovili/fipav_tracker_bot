-- Championship table
CREATE TABLE championships (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    group VARCHAR(10),
    url VARCHAR(255) NOT NULL,
    season VARCHAR(9) NOT NULL,  -- "2025-2026"
    UNIQUE(name, group, season)
);

-- Teams table
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    championship_id INT NOT NULL REFERENCES championships(id) ON DELETE CASCADE,
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
    points_conceded INT DEFAULT 0
);

-- Matches table
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    championship_id INT NOT NULL REFERENCES championships(id) ON DELETE CASCADE,
    match_date TIMESTAMP NOT NULL,
    weekday VARCHAR(10),
    home_team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    away_team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    result VARCHAR(50) NOT NULL,  -- e.g. "3-1" or "25-20,20-25,25-23,25-19"
    city VARCHAR(100),
    address VARCHAR(200)
);