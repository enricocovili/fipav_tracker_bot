-- Let users track several championships and several teams instead of one each.
-- Run once on an existing database:
--   docker exec -i fipav_tracker_postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB" < migrations/001_multi_tracking.sql
BEGIN;

CREATE TABLE IF NOT EXISTS user_championships (
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    championship_id INT NOT NULL REFERENCES championships(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, championship_id)
);

INSERT INTO user_championships (user_id, championship_id)
SELECT id, tracked_championship FROM users
WHERE tracked_championship IS NOT NULL
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS user_teams (
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    team_id INT NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, team_id)
);

INSERT INTO user_teams (user_id, team_id)
SELECT id, tracked_team FROM users
WHERE tracked_team IS NOT NULL
ON CONFLICT DO NOTHING;

ALTER TABLE users DROP COLUMN tracked_championship;
ALTER TABLE users DROP COLUMN tracked_team;

COMMIT;
