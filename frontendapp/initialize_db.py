from frontendapp import webapp
from common import models

def set_db_default_values():
    # This function initialzes the database and populates them 
    # with default values if necessary

    # ensure that the MemcacheConfig table has one and only one
    # entry
    memcache_config_default_capacity = 2.0
    memcache_config_default_replacement_policy = "LRU"
    result_count = webapp.db_session.query(models.MemcacheConfig).count()
    if(result_count == 0):
        new_entry = models.MemcacheConfig(
            capacity_in_mb = memcache_config_default_capacity,
            replacement_policy = memcache_config_default_replacement_policy
        )
        webapp.db_session.add(new_entry)
        webapp.db_session.commit()
    elif(result_count > 1):
        assert False, "the MemcacheConfig table should have only one entry!"
    else:
        pass