class Validators:
    
    @staticmethod
    def valid_integer(value):  # valid_integer changes
        if not value.isdigit():
            return False
        return True

    
    @staticmethod
    def valid_list_of_integers(numbers):  # numbers = 1,2,3
        numbers = numbers.strip().split(",")
        for number in numbers:
            if not Validators.valid_integer(number):
                return False
        return True
    
    
class CommonService:
    @staticmethod
    def default_response(representation, status, msg):
        """
        Custom Response
        """
        output = {"result": representation, "response": {"status": status, "msg": msg}}
        return output

    @staticmethod
    def add_fields(**kwargs):
        """
        Return dictionary of arguements
        """
        return kwargs

   