from jinja2.ext import Extension


class StemKeysExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.filters['stem_keys'] = self.stem_keys

    def stem_keys(self, cookiecutter):
        for key in list(keys()):
            if key.startswith('_pre_prompt_'):
                cookiecutter[key[len('_pre_prompt_'):]] = pop(key)
        return cookiecutter