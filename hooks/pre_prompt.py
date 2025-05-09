import os
import shutil
import sys
import json
import functools
from importlib import import_module

from generate import generate_context
from prompt import prompt_for_config, render_variable


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
            cls.instance = cls._instances[cls]
        return cls._instances[cls]


class PromptProcess(metaclass=SingletonMeta):

    def __init__(self, context, no_input=False):
        self.env = None
        self.context = context
        self.conditions = context['cookiecutter'].pop('__conditions__', {})
        self.cookiecutter = {}
        self.ignored_keys = []
        self.no_input: bool = no_input

    @staticmethod
    def wraps(func_path):
        def decorator(wrapper):
            try:
                module_path, func_name = func_path.rsplit(".", 1)
            except ValueError as e:
                raise ImportError(f"{func_path} doesn't look like a module path")

            try:
                module = sys.modules[module_path]
            except KeyError:
                try:
                    module = import_module(module_path)
                except ImportError as e:
                    raise ImportError(f"Could not import module {module_path}: {e}")

            try:
                function = getattr(module, func_name)
            except AttributeError:
                raise AttributeError(
                    f"Function {func_name} not found in module {module_path}"
                )

            @functools.wraps(function)
            def wrapped(*args, **kwargs):
                return wrapper(PromptProcess.instance, function, *args, **kwargs)

            # Replace the original function with the wrapped version
            setattr(module, func_name, wrapped)

            return wrapper

        return decorator

    @wraps('prompt.render_variable')
    def render_variable(self, func, env, raw, cookiecutter_dict):
        """Initialize the `env` & `cookiecutter` attrs."""
        self.env = env
        self.cookiecutter = cookiecutter_dict
        return func(env, raw, cookiecutter_dict)

    @wraps('prompt.read_user_choice')
    def read_user_choice(self, func, *args, **kwargs):
        return self.apply_read_user_func(func, *args, **kwargs)

    @wraps('prompt.read_user_yes_no')
    def read_user_yes_no(self, func, *args, **kwargs):
        return self.apply_read_user_func(func, *args, **kwargs)

    @wraps('prompt.read_user_variable')
    def read_user_variable(self, func, *args, **kwargs):
        return self.apply_read_user_func(func, *args, **kwargs)

    def prompt_user(self):
        # Get configuration from the user, ignoring keys in ignored_keys
        user_prompts = {
            k: v for k, v in prompt_for_config(self.context, self.no_input).items()
            if k not in self.ignored_keys
        }
        # Return a prefixed prompts
        return {f"_pre_prompt_{k}": v for k, v in user_prompts.items()}

    def apply_read_user_func(self, func, key, *args, **kwargs):
        if key in self.conditions:
            condition = self.conditions[key]
            try:
                is_met = eval(render_variable(self.env, condition, self.cookiecutter))
            except SyntaxError:
                is_met = False
            if not is_met:
                self.ignored_keys.append(key)
                return None
        return func(key, *args, **kwargs)


def copy_pyproject_template():
    # Work around to avoid breaking github actions
    shutil.copyfile(r"./{{project_name}}/pyproject_template.toml", r"./{{project_name}}/pyproject.toml")
    os.remove(r"./{{project_name}}/pyproject_template.toml")


def main():
    copy_pyproject_template()
    initial = generate_context()
    context = generate_context(context_file='pre.json')
    testing: bool = bool(os.getenv("TESTING", False))
    prompt_process = PromptProcess(context, no_input=testing)
    initial['cookiecutter'].update(prompt_process.prompt_user())

    # Write the updated context back to json
    with open('json', 'w') as f:
        json.dump(initial['cookiecutter'], f, indent=2)


if __name__ == "__main__":
    main()