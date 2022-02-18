from memcacheapp import webapp
from common import models

def set_db_default_values():
    # This function initialzes the database and populates them 
    # with default values if necessary
    
    # Remove all entries in MemcacheStats when restarting the memchache
    result_count = webapp.db_session.query(models.MemcacheStats).delete()
    webapp.db_session.commit()
    print("Deleted " + str(result_count) + " entries from MemcacheStats")