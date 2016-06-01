ALTER TABLE image RENAME TO percept;
ALTER SEQUENCE image_id_seq RENAME TO percept_id_seq;
ALTER TABLE percept RENAME COLUMN source_id TO device_id;
ALTER TABLE percept RENAME COLUMN x_resolution TO x_size;
ALTER TABLE percept RENAME COLUMN y_resolution TO y_size;
ALTER TABLE percept ALTER COLUMN x_size DROP NOT NULL;
ALTER TABLE percept ALTER COLUMN y_size DROP NOT NULL;
ALTER TABLE percept ADD COLUMN sample_count bigint;
ALTER TABLE percept ADD COLUMN sample_rate double precision;
ALTER TABLE percept DROP COLUMN depth;
ALTER TABLE tag RENAME TO percept_tag;
ALTER TABLE percept_tag RENAME COLUMN image_id TO percept_id;
ALTER TABLE percept_tag ADD CONSTRAINT percept_tag_percept_id_name_key UNIQUE(percept_id, name);
ALTER TABLE percept_tag RENAME CONSTRAINT tag_image_id_fkey TO percept_tag_percept_id_fkey;
ALTER INDEX tag_image_id_key RENAME TO percept_tag_percept_id_key;
ALTER INDEX image_hash_key RENAME TO percept_hash_key;
ALTER INDEX image_locator_key RENAME TO percept_locator_key;
ALTER INDEX image_pkey RENAME TO percept_pkey;
ALTER TABLE annotation RENAME COLUMN image_id TO percept_id;
ALTER TABLE annotation RENAME CONSTRAINT annotation_image_id_fkey TO annotation_percept_id_fkey;
ALTER TABLE annotation_tag ADD CONSTRAINT annotation_tag_annotation_id_name_key UNIQUE(annotation_id, name);


CREATE TABLE collection (
	id serial PRIMARY KEY,
	name text,
	source text
);

CREATE TABLE percept_collection (
	percept_id integer NOT NULL REFERENCES percept(id),
	collection_id integer NOT NULL REFERENCES collection(id),
	collection_n integer
);

CREATE TYPE provider AS ENUM ('gps', 'network');

CREATE TABLE percept_sensors (
	percept_id integer UNIQUE NOT NULL REFERENCES percept(id),
	location point,
	location_accuracy real,
	bearing real,
	bearing_accuracy real,
	altitude real,
	altitude_accuracy real,
	speed real,
	acceleration double precision[3],
	location_provider provider
);

CREATE TABLE percept_property (
	percept_id integer NOT NULL REFERENCES percept(id),
	name text NOT NULL,
	value text,
	UNIQUE (percept_id, name)
);

CREATE TABLE annotation_property (
	annotation_id integer NOT NULL REFERENCES annotation(id),
	name text NOT NULL,
	value text,
	UNIQUE (annotation_id, name)
);

INSERT INTO percept_sensors(percept_id, location) (SELECT id, location FROM percept WHERE location IS NOT NULL);
ALTER TABLE percept DROP COLUMN location;
ALTER TABLE percept ADD COLUMN locator_new text;
UPDATE percept SET locator_new = builder.newloc FROM (SELECT id, substring(locator::text FROM 1 FOR 2) || '/' || substring(locator::text FROM 3 FOR 2) || '/' || locator::text || '.' || format AS newloc FROM percept) AS builder WHERE percept.id = builder.id;
UPDATE percept SET format = 'image/' || format;
ALTER TABLE percept DROP COLUMN locator;
ALTER TABLE percept RENAME COLUMN locator_new TO locator;
ALTER TABLE percept ADD CONSTRAINT percept_locator_key UNIQUE(locator);
ALTER TABLE percept ALTER COLUMN locator SET NOT NULL;
