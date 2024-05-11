import yaml


class RfidLibrary:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.rfid_data = []
        self.__load_yaml()

    def __load_yaml(self):
        with open(self.data_dir + '/rfids.yaml', 'r') as file:
            self.rfid_data = yaml.safe_load(file)

    def get_data(self, rfid_uid):
        for item in self.rfid_data:
            if item['id'] == rfid_uid:
                return item
