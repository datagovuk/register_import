"""
A script to extract the register records from the register register and
create matching datasets on data.gov.uk (if they don't already exist).
"""
from urlparse import urljoin

import requests
import ckanapi


# A map between the register organisation names, and the dgu organisation names
ORGANISATIONS = {
    'foreign-commonwealth-office': 'foreign-and-commonwealth-office',
    'government-digital-service': 'government-digital-services'
}

def lookup_organisation(org_name):
    """ Map the register organisation names to the DGU names where they
        don't line up. """
    return ORGANISATIONS.get(org_name, org_name)


def make_description(props):
    """ Create a description for the dataset using the register properties from
        the register.json file """
    return u"""
{text}

Registers - Registers are lists of information. Each register is the most
reliable list of its kind. If you wish to know more about registers, please
visit the registers guidance at
[https://www.gov.uk/government/publications/registers/registers](https://www.gov.uk/government/publications/registers/registers)

Fields in this register - {field_string}

    """.format(**props).strip()



def build_resource_list(register_name):
    """ For the named register, return a list of resource dictionaries
        containing information about the TTL, CSV and JSON format downloads
        as well as providing a link to the register front-end """
    resources = []

    base_url = 'https://{}.register.gov.uk/'.format(register_name)
    formats = ['csv', 'json', 'ttl']

    resources.append({
        'description': 'Register home page',
        'url': base_url,
        'format': 'HTML'
    })

    for fmt in formats:
        resources.append({
            'description': 'Register Entries ({})'.format(fmt.upper()),
            'url': urljoin(base_url, 'records.{}?page-size=5000'.format(fmt)),
            'format': fmt.upper()
        })
    return resources


def get_current_registers(phase='beta'):
    """ Download all of the entries from the register register for a specific
        phase and convert the register info into CKAN style package json """
    url = "https://register.register.gov.uk/records.json?page-size=500"
    r = requests.get(url)
    for name, props in r.json().iteritems():
        if not props.get('phase') == phase:
            continue

        props['field_string'] = ', '.join(props.get('fields'))

        yield {
            'title': '{} Register'.format(name.title()).replace('-', ' '),
            'name': '{name}-register'.format(name=name),
            'register': 'true',
            'owner_org': lookup_organisation(props.get('registry')),
            'notes': make_description(props),
            'resources': build_resource_list(name),
            'license_id': 'uk-ogl'
        }

def is_register(data):
    extra = [e for e in data.get('extras', {}) if e.get('key') == 'register']
    if not extra:
        return False
    return extra[0].get('value') == 'true'

def write_register(register_name, data):
    """ Using the provided name, write the data parameter as a new dataset on
        data.gov.uk.  If the name is in use, check if it is a register and
        abort/create as necessary """
    ckan = ckanapi.RemoteCKAN('https://test.data.gov.uk', apikey='')

    res = ckan.action.package_search(
        q='name:{}'.format(register_name)
    )

    if res['count'] > 0:
        print 'Dataset {} already exists, checking'.format(register_name)

        # Iterate through all of the results looking to see if any are a
        # register at which point we will just happily return.  If not then
        # we'll create one by incrementing the number.  We *should* only get
        # one or zero back from this call, but just to be sure....
        for possible_register in res['results']:
            # TODO: need to check extras here......
            if is_register(possible_register):
                print '  Existing register {} valid'.format(register_name)
                return

        new_name = '{}-{}'.format(register_name, res['count'] + 1 )
        data['name'] = new_name
        write_register( new_name, data)
    else:
        print '  Creating dataset for register {}'.format(register_name)
        try:
            ckan.action.package_create(**data)
            print '  ... created'
        except ckanapi.errors.ValidationError, e:
            print '  Looks like the URL was already in use'


def main():
    """ Get the registers, create the datasets """
    registers = get_current_registers()
    for register in registers:
        register_name = register.get('name')
        write_register(register_name, register)

