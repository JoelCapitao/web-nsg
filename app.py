import os
from flask import render_template, request, flash, redirect, url_for, Response, session
from model import app, User, Customer, Project
from netscriptgen import NetScriptGen, Integer
from werkzeug import secure_filename
from validationForm import ProjectForm
from flask.ext.session import Session
SESSION_TYPE = 'redis'
SECRET_KEY = 'develop'

@app.route('/project/new', methods=['GET','POST'])
def project_new():
    form = ProjectForm(request.form)
    print(form.validate())
    if request.method == 'POST' and form.validate():

        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], request.form['client'], request.form['subproject_name'])
        os.makedirs(project_folder, exist_ok=True)

        excel_file = request.files['excel_file']
        excel_file_path = os.path.join(project_folder, secure_filename(excel_file.filename))
        excel_file.save(excel_file_path)

        template_file = request.files['template_file']
        template_file_path = os.path.join(project_folder, secure_filename(template_file.filename))
        template_file.save(template_file_path)

        project = dict()
        for item in ('client', 'project_name', 'subproject_name'):
            project[item] = request.form[item]
        for item, path in [('excel_file', 'excel_file_path'), ('template_file', 'template_file_path')]:
            project[item] = path
        session['data'] = project
        print(project)
        try:
            equipments, wb = nsg_processing(excel_file_path, template_file_path)
        except:
            exit()
            #TODO: Add a return page that handles this error


        for equipment in equipments:
            equipment.save_script_as(project_folder, equipment.get_value_of_var('Hostname', wb))
        return render_template('generation_preview.html', equipments=equipments, iterator=Integer(0), wb=wb)

    return render_template('project.html', form=form)


@app.route('/project/add', methods=['GET','POST'])
def project_add():
    form = ProjectForm(request.form)
    print(form.validate())
    if request.method == 'POST' and form.validate():
        excel_file = request.files['excel_file']
        excel_file = secure_filename(excel_file.filename)
        template_file = request.files['template_file']
        template_file = secure_filename(template_file.filename)

        try:
            equipments, wb = nsg_processing(excel_file, template_file)
        except:
            exit()
            #TODO: Add a return page that handles this error

        project_data = session.get('data')

        project = Project(project_data['client'],
                          project_data['project_name'],
                          project_data['subproject_name'],
                          project_data['excel_file'],
                          project_data['template_file']
                          )
        post_add = project.add(project)

        if not post_add:
            project_folder = os.path.join(app.config['UPLOAD_FOLDER'], project.id)
            os.makedirs(project_folder, exist_ok=True)
            excel_file_path = os.path.join(project_folder, excel_file)
            excel_file.save(excel_file_path)
            template_file_path = os.path.join(project_folder, template_file)
            template_file.save(template_file_path)
            flash("Add was successful")
            for equipment in equipments:
                equipment.save_script_as(project_folder, equipment.get_value_of_var('Hostname', wb))
            return render_template('generation_preview.html', equipments=equipments, iterator=Integer(0), wb=wb)
        else:
            error = post_add
            flash(error)
    return render_template('project.html', form=form)


def nsg_processing(excel_worbook, template_file):
    excel_wb = excel_worbook
    template = open(template_file, 'r', -1, 'UTF-8').read()
    nsg = NetScriptGen(excel_wb, template)
    nsg.extract_data()
    equipments = nsg.get_all_equipments()
    print(equipments)
    return equipments, nsg.workbook




@app.route('/user')
def user_display_all():
    user = User.query.all()
    return render_template('user_display_all.html', user=user)


@app.route('/user/display/<id>', methods=['GET','POST'])
def user_display(id):
    user = User.query.get(id)
    if user is None:
        flash("The user does not exist in the database")
        return redirect(url_for('user_display_all'))
    return render_template('user_display.html', user=user, alert='None', message='')


@app.route('/user/update/<id>', methods=['GET','POST'])
def user_update(id):
    user = User.query.get(id)
    if user == None:
        flash("The user does not exist in the database")
        return redirect(url_for('user_display_all'))
    if request.method == 'POST':
        user = User(request.form['firstname'],
                    request.form['lastname'],
                    request.form['email'],
                    request.form['password'],
                    request.form['quadri'],
                  )
        user_update = user.update(user)
        if not user_update:
            flash("Update was successful")
            return redirect(url_for('user_display', id=id))
        else:
            error=user_update
            flash(error)
    return render_template('user_update.html', user=user, alert='None', message='')



@app.route('/user/delete/<id>')
def user_delete(id):
    user = User.query.get(id)
    if user == None:
        flash("This entry does not exist in the database")
        return redirect(url_for('user_display_all'))
    post_delete = user.delete(user)
    if not post_delete:
        flash("User was deleted successfully")
    else:
        error = post_delete
        flash(error)
    return redirect(url_for('user_display_all'))


@app.route('/user/add', methods=['GET','POST'])
def user_add():
    if request.method == 'POST':
        user = User(request.form['firstname'],
                    request.form['lastname'],
                    request.form['email'],
                    request.form['password'],
                    request.form['quadri'],
                  )
        post_add = user.add(user)
        if not post_add:
            flash("Add was successful")
            return redirect(url_for('user_display_all'))
        else:
            error = post_add
            flash(error)
    return render_template('new_user.html')


@app.route('/customer')
def customer_display_all():
    customer = Customer.query.all()
    return render_template('customer_display_all.html', customer=customer)

@app.route('/customer/add', methods=['GET','POST'])
def customer_add():
    if request.method == 'POST':
        customer = Customer(request.form['firstname'],
                            request.form['lastname'],
                            request.form['mail'],
                            request.form['company'],
                            request.form['landline'],
                            request.form['function']
                            )
        post_add = customer.add(customer)
        if not post_add:
            flash("Add was successful")
            return redirect(url_for('customer_display_all'))
        else:
            error = post_add
            flash(error)
    return render_template('customer_user.html')


@app.route('/customer/update/<id>', methods=['GET','POST'])
def customer_update(id):
    customer = Customer.query.get(id)
    if customer == None:
        flash("The user does not exist in the database")
        return redirect(url_for('customer_display_all'))
    if request.method == 'POST':
        customer = Customer(request.form['firstname'],
                            request.form['lastname'],
                            request.form['mail'],
                            request.form['company'],
                            request.form['landline'],
                            request.form['function']
                            )
        customer_update = customer.update(customer)
        if not customer_update:
            flash("Update was successful")
            return redirect(url_for('customer_display', id=id))
        else:
            error = user_update
            flash(error)
    return render_template('customer_update.html', customer=customer, alert='None', message='')

@app.route('/customer/delete/<id>')
def customer_delete(id):
    customer = Customer.query.get(id)
    if customer == None:
        flash("This entry does not exist in the database")
        return redirect(url_for('customer_display_all'))
    post_delete = customer.delete(customer)
    if not post_delete:
        flash("Customer was deleted successfully")
    else:
        error = post_delete
        flash(error)
    return redirect(url_for('customer_display_all'))

@app.route('/customer/display/<id>', methods=['GET','POST'])
def customer_display(id):
    customer = Customer.query.get(id)
    if customer is None:
        flash("The user does not exist in the database")
        return redirect(url_for('customer_display_all'))
    return render_template('customer_display.html', customer=customer, alert='None', message='')

@app.route('/file/<id>/<filename>')
def return_file(id, filename):
    file = get_file(id, filename)
    return Response(file, mimetype="text/plain")

def get_file(id, filename):
    try:
        file = os.path.join(app.config['UPLOAD_FOLDER'], id, filename)
        return open(file).read()
    except IOError as exc:
        return str(exc)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5004)
