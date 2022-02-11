
class Singleton:
    def __init__(self, this_instance):
        self._this_instance = this_instance

    def instance(self):
        try:
            return self._instance
        except AttributeError:
            self._instance = self._this_instance()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

