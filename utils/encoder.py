import json
import decimal
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)

class DecimalDecoder(json.JSONEncoder):
    def decode(self, o):
        if isinstance(o, basestring):
            if o[:7] == 'Decimal':      
                n = o[9:] + o[:-2]          
                return decimal.Decimal(n)
        return super(DecimalDecoder, self).decode(o)