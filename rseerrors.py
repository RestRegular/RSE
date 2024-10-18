class TargetCountMismatchedError(Exception):
    def __init__(self, target_count: int, given_count: int):
        super().__init__(f'The target count [{target_count}] is mismatched with the given count [{given_count}]')


class InstructionNotFoundError(Exception):
    def __init__(self, instruction: str):
        super().__init__(f'[{instruction}]: This instruction is not defined in RSE standard instruction library.')


class WrongInstructionPartError(Exception):
    def __init__(self, instruction_part: str):
        super().__init__(f'[{instruction_part}]: This part of instruction is wrong.')


class InstructionParamCountMismatchedError(Exception):
    def __init__(self, instruction_head: str, need_count: int, given_count: int):
        super().__init__(f'[{instruction_head}]: This instruction need {need_count} params, but received {given_count}.')


class InvalidFilePathError(Exception):
    def __init__(self, path: str):
        super().__init__(f'[{path}]: This path is invalid.')

