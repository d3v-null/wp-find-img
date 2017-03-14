import sqlite3

class DBWrapper(object):
    # table names
    tname_scraped_imgs = "scraped_images"
    tname_image_sighting = "image_sightings"

    # col names
    cname_img_id = "img_id"
    cname_img_url = "img_url"
    cname_img_checksum = 'img_checksum'
    cname_dhash = "dhash"
    cname_length = 'length'
    cname_width = 'width'
    cname_size = 'size'
    cname_sighting_id = 'sighting_id'
    cname_page_url = 'page_url'
    cname_scrape_time = 'scrape_time'

    # mapping of image meta keys to column names
    meta_cnames = [
        ('url', [cname_img_url]),
    ]

    def __init__(self, dbfile):
        self.conn = sqlite3.connect(dbfile)
        self.init_tables()

    def init_tables(self):
        c = self.conn.cursor()
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS {tn_si} (
                {cn_ii} INT NOT NULL PRIMARY KEY,
                {cn_iu} TEXT,
                {cn_cs} TEXT,
                {cn_dh} TEXT,
                {cn_l} INT,
                {cn_w} INT,
                {cn_s} INT
            );
            """.format(
                tn_si=self.tname_scraped_imgs,
                cn_ii=self.cname_img_id,
                cn_iu=self.cname_img_url,
                cn_cs=self.cname_img_checksum,
                cn_dh=self.cname_dhash,
                cn_l=self.cname_length,
                cn_w=self.cname_width,
                cn_s=self.cname_size
            )
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS {tn_is} (
                sighting_id INT NOT NULL PRIMARY KEY,
                {cn_ii} INT NOT NULL,
                {cn_pu} TEXT,
                {cn_st} TEXT
            )
            """.format(
                tn_is=self.tname_image_sighting,
                cn_ii=self.cname_img_id,
                cn_pu=self.cname_page_url,
                cn_st=self.cname_scrape_time
            )
        )

    def close(self):
        self.conn.commit()
        self.conn.close()

    def add_sighting(self, page_url, scrape_time, image_meta):
        c = self.conn.cursor()

        img_url = image_meta.get('url')
        assert img_url, "no image url provided in image_meta: {meta}".format(
            meta=image_meta
        )

        img_sel_sql = 'SELECT * FROM {tn_si} WHERE {cn_iu}=:iu'.format(
            tn_si=self.tname_scraped_imgs,
            cn_iu=self.cname_img_url,
        )

        img_checksum = image_meta.get('checksum')
        if img_checksum:
            img_sel_sql += ' AND {cn_cs}=:cs'.format(
                cn_cs=self.cname_img_checksum,
            )

        # have we seen the img url before?
        c.execute(
            img_sel_sql, {
                'iu':img_url,
                'cs':img_checksum
            }
        )
        images = c.fetchall()

        img_pkey = None
        if(images):
            assert len(images) == 1, \
                "should only be one image with a given checksum and url"
            img_pkey = images[0][self.cname_img_id]
        else:
            # create image and retrieve pkey
            cols = []
            for meta_key, cnames in self.meta_cnames:
