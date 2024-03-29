from dicomanonymizer import *

def main():

  # Create a list of tags object that should contains id, type and value
  fields = [
    { # Replaced by Anonymized
      'id': (0x0040, 0xA123),
      'type': 'LO',
      'value': 'Annie de la Fontaine',
    },
    { # Replaced with empty value
      'id': (0x0008, 0x0050),
      'type': 'TM',
      'value': 'bar',
    },
    { # Deleted
      'id': (0x0018, 0x4000),
      'type': 'VR',
      'value': 'foo',
    }
  ]

  # Create a readable dataset for pydicom
  data = pydicom.Dataset()

  # Add each field into the dataset
  for field in fields:
    data.add_new(field['id'], field['type'], field['value'])

  anonymize_dataset(data)

if __name__ == "__main__":
    main()