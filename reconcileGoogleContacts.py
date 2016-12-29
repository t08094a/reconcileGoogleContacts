#!/usr/bin/python

from __future__ import print_function

import atom
import oauth2client
import gdata
import gdata.data
import gdata.contacts
import gdata.contacts.client
import gdata.gauth

import oauth2client.client
import oauth2client.file


def get_credentials():
    """
    Gets google api credentials, or generates new credentials if they don't exist or are invalid.
    :rtype: oauth2client.client.OAuth2Credentials
    """
    credentialFilename = 'credentials.dat'
    scope = ['https://www.googleapis.com/auth/contacts', 'https://www.google.com/m8/feeds', 'https://www.google.com/m8/feeds/contacts/{userEmail}/full']

    flow = oauth2client.client.flow_from_clientsecrets('client_secret.json', scope)
    flow.user_agent = 'reconcileGoogleContacts'

    storage = oauth2client.file.Storage(credentialFilename)
    credentials = storage.get()

    if not credentials or credentials.invalid:
        credentials = oauth2client.tools.run_flow(flow, storage, None)
        print('Storing credentials to ' + credentialFilename)

    return credentials


def get_client():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        gdata.contacts.client.ContactsClient, the obtained credential.
        :rtype: gdata.contacts.client.ContactsClient
    """

    credentials = get_credentials()

    auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)

    query = gdata.contacts.client.ContactsQuery()
    query.max_results = 1000

    contact_client = gdata.contacts.client.ContactsClient(query)
    auth2token.authorize(contact_client)

    return contact_client


def printEntries(feed):
    """Prints out the contents of a feed to the console.
        Args:
          feed: A gdata.contacts.data.ContactsFeed
    """

    if not feed:
        return

    for entry in feed.entry:
        printEntry(entry)

    # feed can have siblings with more entries
    next = feed.GetNextLink()
    if next:
        print('further more entries exist: ' + next.href)


def printEntry(entry):
    """Prints out the contents of a single Entry to the console.
    Args:
      entry: A gdata.contacts.ProfilesEntry
    """

    print('\n%s' % entry.title.text)

    print('Id: %s' % entry.id.text)
    print('language: %s' % getValueOfXmlElement(entry.language, 'text'))

    if entry.name:
        print('given_name: %s' % getValueOfXmlElement(entry.name.given_name, 'text'))
        print('additional_name: %s' % getValueOfXmlElement(entry.name.additional_name, 'text'))
        print('family_name: %s' % getValueOfXmlElement(entry.name.family_name, 'text'))
        print('name_prefix: %s' % getValueOfXmlElement(entry.name.name_prefix, 'text'))
        print('name_suffix: %s' % getValueOfXmlElement(entry.name.name_suffix, 'text'))
        print('full_name: %s' % getValueOfXmlElement(entry.name.full_name, 'text'))

    for address in entry.postal_address:
        print('postal_address: %s' % getValueOfXmlElement(address))
        # rel = gdata.data.WORK_REL, primary = 'true',
        # street = gdata.data.Street(text='1600 Amphitheatre Pkwy'),
        # city = gdata.data.City(text='Mountain View'),
        # region = gdata.data.Region(text='CA'),
        # postcode = gdata.data.Postcode(text='94043'),
        # country = gdata.data.Country(text='United States'))

    print('structured_postal_address: %s' % getValueOfXmlElement(entry.structured_postal_address))
    print('Gender: %s' % getValueOfXmlElement(entry.gender))
    print('Occupation: %s' % getValueOfXmlElement(entry.occupation))
    print('Nickname: %s' % getValueOfXmlElement(entry.nickname))
    for email in entry.email:
        print('Email {} ({}): {} {}'.format(email.rel, email.display_name, getValueOfXmlElement(email.address), ('' if email.primary == 'true' else '(primary)')))
    print('Birthday: %s' % getValueOfXmlElement(entry.birthday))
    print('Etag: %s' % getValueOfXmlElement(entry.etag))
    for phone in entry.phone_number:
        print('Phone Number: %s' % getValueOfXmlElement(phone))
        print('Phone {} ({}): {} {} {}'.format(phone.rel, phone.label, phone.text, phone.uri, ('' if email.primary == 'true' else '(primary)')))
    print('priority: %s' % getValueOfXmlElement(entry.priority))
    print('text: %s' % getValueOfXmlElement(entry.text))
    print('title: %s' % getValueOfXmlElement(entry.title))
    print('content: %s' % getValueOfXmlElement(entry.content, 'text'))  # = notes

    for user_defined_field in entry.user_defined_field:
        print('UserDefinedField: %s %s' % (user_defined_field.key, user_defined_field.value))


def getValueOfXmlElement(xmlElement, fieldName = None):
    if fieldName:
        result = str(getattr(xmlElement, fieldName, ''))
        return result

    if isinstance(xmlElement, atom.AtomBase):
        if xmlElement._attributes:
            resultStr = ''
            for attr in xmlElement.extension_attributes:
                tmpStr = resultStr + getattr(xmlElement, attr, '')
                if len(tmpStr) and len(resultStr):
                    resultStr = resultStr + '; ' + tmpStr
                else:
                    resultStr = tmpStr

            return resultStr

    if(isinstance(xmlElement, gdata.data.StructuredPostalAddress)):
        pass
    elif isinstance(xmlElement, atom.core.XmlElement):
        return xmlElement.text
    elif isinstance(xmlElement, atom.core.XmlElement):
        return xmlElement.value
    elif isinstance(xmlElement, gdata.contacts.Birthday):
        return xmlElement.when
    elif isinstance(xmlElement, list) and xmlElement:
        return xmlElement[0]
    else:
        return str(xmlElement)


def update_contact_name(gd_client, contact_url):

    print('update_contact_name: {}'.format(contact_url))

    # first retrieve the contact to modify from the api
    entry = gd_client.GetContact(contact_url)
    entry.name.full_name.text = 'full_name'
    entry.name.given_name.text = 'given_name'
    entry.name.family_name.text = 'family_name'

    # entry.name.additional_name = gdata.data.AdditionalName(text='') # 2. Vorname
    # entry.name.name_prefix = gdata.data.NamePrefix(text='') # Vorsilbe
    # entry.name.name_suffix = gdata.data.NameSuffix(text='') # Endsilbe

    ## Funktioniert nicht!
    #entry.gender = gdata.contacts.Gender(value='male')
    #entry.occupation = gdata.contacts.Occupation(text='Carpender')

    #entry.etag = '*'

    try:
        updated_entry = gd_client.Update(entry)
        print('Updated: {}'.format(updated_entry.updated.text))
        return updated_entry

    except gdata.client.RequestError, e:
        if(e.status == 412):
            # Etag mismatch: handle the exception
            print('Error: Etag mismatch')
            pass
        elif(e.status == 401):
            print('Error: 401')
            pass
    except AttributeError, e:
        print('Error: {}'.format(e))
        pass

    return None

def main():
    contact_client = get_client()  # type: gdata.contacts.client.ContactsClient

    feed = contact_client.GetContacts()
    printEntries(feed)

    update_contact_name(contact_client, 'http://www.google.com/m8/feeds/contacts/testjochenfaehnlein%40gmail.com/base/52956ed38d319b0e')

if __name__ == '__main__':
    main()
