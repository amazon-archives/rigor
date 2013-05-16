CREATE TABLE image (
    id serial PRIMARY KEY,
    locator uuid UNIQUE NOT NULL,
    hash text UNIQUE NOT NULL,
    stamp timestamp with time zone,
    x_resolution integer NOT NULL,
    y_resolution integer NOT NULL,
    format text NOT NULL,
    depth smallint NOT NULL,
    location point
);

CREATE TABLE annotation (
    id serial PRIMARY KEY,
    image_id integer NOT NULL REFERENCES image(id),
    confidence integer NOT NULL,
    stamp timestamp with time zone DEFAULT now() NOT NULL,
    boundary polygon,
    domain text NOT NULL,
    model text
);
CREATE UNIQUE INDEX annotation_unique ON annotation USING btree (image_id, md5((boundary)::text), domain);

CREATE TABLE tag (
    image_id integer NOT NULL REFERENCES image(id),
    name text NOT NULL
);
CREATE INDEX tag_image_id_key ON tag USING btree (image_id);

CREATE TABLE annotation_tag (
    annotation_id integer NOT NULL REFERENCES annotation(id),
    name text NOT NULL
);
CREATE INDEX annotation_tag_annotation_id_key ON annotation_tag USING btree (annotation_id);

CREATE TABLE meta (
    key text PRIMARY KEY,
    value text
);

INSERT INTO meta (key, value) VALUES ('patch_level', 0);
