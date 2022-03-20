from managerapp import webapp
from common import models

def set_db_default_values():
    # This function initialzes the database and populates them 
    # with default values if necessary. Do all initialization here because
    # memcache app is being launched ealier
    # ensure that the MemcacheConfig table has one and only one
    # entry
    memcache_config_default_capacity = 2.0
    memcache_config_default_replacement_policy = "LRU"
    result_count = local_session.query(models.MemcacheConfig).count()
    if(result_count == 0):
        new_entry = models.MemcacheConfig(
            capacity_in_mb = memcache_config_default_capacity,
            replacement_policy = memcache_config_default_replacement_policy
        )
        local_session.add(new_entry)
        local_session.commit()
    elif(result_count > 1):
        assert False, "the MemcacheConfig table should have only one entry!"
    else:
        result = local_session.query(models.MemcacheConfig).first()
        result.replacement_policy = memcache_config_default_replacement_policy
        result.capacity_in_mb = memcache_config_default_capacity
        local_session.commit()
