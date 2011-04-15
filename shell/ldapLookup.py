#!/usr/bin/env python

"""A module which allows for querying the PSU LDAP server."""

import ldap


class PsuLdap(object):
    base_dn = u'dc=psu,dc=edu'
    host = 'dirapps.aset.psu.edu'

    def member_search(self, uid):
        """Returns the ldap search results for the given uid. A single result
            is returned
            """
        #conn = ldap.open(self.host)
        conn = ldap.initialize('ldap://%s:389' % self.host)
        search_filter = '(uid=%s)' % uid
        try:
            entry = conn.search_s(self.base_dn, ldap.SCOPE_SUBTREE,
                filterstr=search_filter)
            if not entry:
                entry = ('', {},)
            else:
                # We only want the first entry.
                entry = entry[0] # Results in: (dn, attrs)
        except ldap.SERVER_DOWN:
            print "LDAP server @ %s seems to be unresponsive." % self.host
            
        attribute_data = entry[1]
        return attribute_data
    

if __name__ == '__main__':
    test = PsuLdap()
    paul = test.member_search('par117')
    import pdb; pdb.set_trace()

