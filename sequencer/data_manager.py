import numpy as np
from PIL import Image
import json

class MyData:
    def __init__(self, image, numbers, json_data):
        self.image = image
        self.numbers = numbers
        self.json_data = json_data

    def to_dict(self):
        return {
            'image': np.array(self.image),
            'numbers': self.numbers,
            'json_data': np.string_(json.dumps(self.json_data))
        }

    @classmethod
    def from_dict(cls, data_dict):
        image = Image.fromarray(data_dict['image'])
        numbers = data_dict['numbers']
        json_data = json.loads(data_dict['json_data'].item().decode('utf-8'))
        return cls(image, numbers, json_data)

# Create an instance of MyData
image = Image.open('path/to/your/image.jpg')
numbers = np.random.random(size=(100,))
json_data = {"key1": "value1", "key2": [1, 2, 3]}

my_data = MyData(image, numbers, json_data)
data_dict = my_data.to_dict()

# Save to a .npz file
np.savez('data.npz', **data_dict)

# Load from the .npz file
data = np.load('data.npz')

# Convert the loaded data to a dictionary
data_dict = {key: data[key] for key in data}

# Reconstruct the class instance
loaded_data = MyData.from_dict(data_dict)

# Verify the data
print(loaded_data.image)
print(loaded_data.numbers)
print(loaded_data.json_data)
