import os
from flask import render_template, request, flash, redirect, url_for, Response, session, send_file
from model import app, User, Customer, Project, lastIDof
from netscriptgen import NetScriptGen, Integer
from werkzeug import secure_filename
from shutil import move
from validationForm import ProjectForm
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from time import localtime, time
from flask.ext.session import Session
from io import BytesIO
SESSION_TYPE = 'redis'
SECRET_KEY = 'develop'

@app.route('/project/new', methods=['GET','POST'])
def project_new():
    form = ProjectForm(request.form)
    print(form.validate())
    if request.method == 'POST' and form.validate():

        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], '{0}-{1}'.format(request.form['client'], request.form['subproject_name']))
        session['project_folder'] = project_folder
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
            equipments, wb, hostnames = nsg_processing(excel_file_path, template_file_path)
        except:
            exit()
            #TODO: Add a return page that handles this error

        session['hostnames'] = hostnames
        for equipment in equipments:
            equipment.save_script_as(project_folder, equipment.get_value_of_var('Hostname', wb))
        return render_template('generation_preview.html', equipments=equipments, iterator=Integer(0), wb=wb)

    return render_template('project.html', form=form)


@app.route('/project/add', methods=['GET','POST'])
def project_add():
    if request.method == 'POST':
        project_data = session.get('data')
        project = Project(project_data['client'],
                          project_data['project_name'],
                          project_data['subproject_name'],
                          project_data['excel_file'],
                          project_data['template_file']
                          )
        post_add = project.add(project)
        id_project = '3'

        if not post_add:
            print(project.client)
            new_project_folder = os.path.join(app.config['UPLOAD_FOLDER'], id_project)
            move(session['project_folder'], new_project_folder)

            for hostname in session['hostnames']:
                list_of_files = list()
                check = request.form.get(hostname, default=False, type=bool)
                if check:
                    list_of_files.append(hostname + '.txt')
            list_of_files.append(project_data['excel_file'] + '.xlsx')
            list_of_files.append(project_data['template_file'] + '.txt')

            name = dict()
            for item in ('client', 'project_name', 'subproject_name'):
                name[item] = project_data[item]
            memory_file, attachment_filename = zip_file(list_of_files, name)
            send_file(memory_file, attachment_filename=attachment_filename, as_attachment=True)

            return render_template('project_display_all.html', project=project)
        else:
            error = post_add
            flash(error)
    return render_template('project.html')


def nsg_processing(excel_worbook, template_file):
    excel_wb = excel_worbook
    template = open(template_file, 'r', -1, 'UTF-8').read()
    nsg = NetScriptGen(excel_wb, template)
    nsg.extract_data()
    equipments = nsg.get_all_equipments()
    hostnames = nsg.get_all_equipment_names()
    return equipments, nsg.workbook, hostnames


@app.route('/project')
def project_display_all():
    project = Project.query.all()
    for p in project:
        print(p.id)
        print(p.client)
        print(p.projectName)
    return render_template('project_display_all.html', project=project)


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

@app.route('/file/<filename>')
def return_file(filename):
    folder = session['project_folder']
    file = get_file(folder, filename + '.txt')
    return Response(file, mimetype="text/plain")

def get_file(folder, filename):
    try:
        file = os.path.join(folder, filename)
        return open(file).read()
    except IOError as exc:
        return str(exc)


def zip_file(list_of_files, name):
    memory_file = BytesIO()
    if name['subproject_name']:
        zf_name = "scripts-{0}-{1}-{2}".format(name['client'], name['project_name'], name['subproject_name'])
    else:
        zf_name = "scripts-{0}-{1}".format(name['client'], name['project_name'])
    with ZipFile(memory_file, 'w') as zf:
        for file in list_of_files:
            data = ZipInfo(file)
            data.date_time = localtime(time())[:6]
            data.compress_type = ZIP_DEFLATED
            zf.writestr(data, file)
    return memory_file, zf_name


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5004)
