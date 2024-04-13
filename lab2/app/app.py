from flask import Flask, render_template, request, make_response

app = Flask(__name__)
application = app

OPERATIONS = {
    '+': lambda x, y: x + y,
    '-': lambda x, y: x - y,
    '*': lambda x, y: x * y,
    '/': lambda x, y: x / y
}

@app.route('/')
def index():
    url = request.url
    return render_template('index.html', url=url)

@app.route('/args')
def args():
    return render_template('args.html')

@app.route('/headers')
def headers():
    return render_template('headers.html')

@app.route('/cookies')
def cookies():
    response = make_response(render_template('cookies.html'))
    if 'biscuit' in request.cookies:
        response.delete_cookie('biscuit')
    else:
        response.set_cookie('biscuit', value='100 gramm')
    return response

@app.route('/form', methods=['GET','POST'])
def form():
    return render_template('form.html')

@app.route('/calculator', methods=['GET','POST'])
def calculator():
    result = ''
    error = ''
    if request.method == 'POST':
        try:
            operation = request.form.get('operation')
            oper1 = int(request.form.get('oper1'))
            oper2 = int(request.form.get('oper2'))

            result = OPERATIONS[operation](oper1, oper2)
        except ValueError:
            error = 'Вычисление возможно только с числами'
            return render_template('calculator.html', error=error, result=result, operations=OPERATIONS.keys())
        except ZeroDivisionError:
            error = 'На ноль делить нельзя'
        except KeyError:
            error = 'Неизвестная математическая операция'

    return render_template('calculator.html', error=error, result=result, operations=OPERATIONS.keys())


def checkNumber(number):
    digs = sum(1 for i in number if i.isdigit())
    if digs == 10:
        return 10 
    if digs == 11:
        if (number[1] == '7' and number[0] == '+') or (number[0] == '8'):
            return 11
    return 0   

@app.route('/phone', methods=['GET','POST'])
def phone():
    result = ''
    error = ''
    symbols ='( ).-'
    if request.method == 'POST':
        number = request.form.get('phone')
        if checkNumber(number) == 10:
            for i in range(len(number)):
                if number[i].isdigit():
                    result += number[i]
                elif number[i] not in symbols:
                    error = "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
                    result=''
                    return render_template('phone.html', error=error, result=result)  
        elif checkNumber(number) == 11:
            for i in range(1,len(number)):
                if i == 1 and number[i] == '7':
                    continue
                if number[i].isdigit():
                    result += number[i]
                elif number[i] not in symbols:
                    error = "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
                    result=''
                    return render_template('phone.html', error=error, result=result)           
        else:
            error = 'Недопустимый ввод. Неверное количество цифр'
            return render_template('phone.html', error=error, result=result)
        result = '8-{}{}{}-{}{}{}-{}{}-{}{}'.format(*result)
    return render_template('phone.html', error=error, result=result)