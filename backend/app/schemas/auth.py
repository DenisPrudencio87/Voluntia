from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Login(Input):
    correo: EmailStr
    clave: str = Field(min_length=1, max_length=128)


class Register(Login):
    clave: str = Field(min_length=12, max_length=128)
    confirmacion: str = Field(min_length=12, max_length=128)

    @model_validator(mode='after')
    def matching_passwords(self):
        if self.clave != self.confirmacion:
            raise ValueError('Las contraseñas no coinciden')
        return self


class EmailInput(Input):
    correo: EmailStr


class TokenInput(Input):
    token: str = Field(min_length=20, max_length=200)


class ResetPassword(TokenInput):
    clave: str = Field(min_length=12, max_length=128)
    confirmacion: str = Field(min_length=12, max_length=128)

    @model_validator(mode='after')
    def matching_passwords(self):
        if self.clave != self.confirmacion:
            raise ValueError('Las contraseñas no coinciden')
        return self


class ChangePassword(Input):
    clave_actual: str = Field(min_length=1, max_length=128)
    clave: str = Field(min_length=12, max_length=128)
    confirmacion: str = Field(min_length=12, max_length=128)

    @model_validator(mode='after')
    def matching_passwords(self):
        if self.clave != self.confirmacion:
            raise ValueError('Las contraseñas no coinciden')
        return self
