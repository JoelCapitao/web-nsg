import os
from flask import render_template, request, flash, redirect, url_for, Response, session, send_file, send_from_directory
from model import app, User, Customer, Project, lastProject, ProjectVersioning
from netscriptgen import NetScriptGen, Integer
from werkzeug import secure_filename
from shutil import move
from validationForm import ProjectForm
from zip_list_of_files_in_memory import zip_file
SESSION_TYPE = 'redis'
SECRET_KEY = 'develop'

@app.route('/project/new', methods=['GET','POST'])
def project_new():
    form = ProjectForm(request.form)
    if request.method == 'POST' and form.validate():

        _folder = '{0}-{1}'.format(request.form['client'], request.form['subproject_name'])
        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], _folder)
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
        for item, path in [('excel_file', excel_file.filename), ('template_file', template_file.filename)]:
            project[item] = path
        session['data'] = project
        try:
            equipments, wb, hostnames = nsg_processing(excel_file_path, template_file_path)
        except:
            exit()
            #TODO: Add a return page that handles this error

        session['hostnames'] = hostnames

        data_of_equipments = list()

        total_of_var = {'to_fill': 0, 'filled': 0}
        for equipment in equipments:
            equipment.save_script_as(project_folder, equipment.get_value_of_var('Hostname', wb))
            total_of_var['to_fill'] += equipment.get_resolved_var() + equipment.get_unresolved_var()
            total_of_var['filled'] += equipment.get_resolved_var()
            _data_of_equipment = dict()
            for item in ('Hostname', 'Equipment', 'Type'):
                _data_of_equipment[item] = equipment.get_value_of_var(item, wb)
            _data_of_equipment['filling_ratio'] = equipment.get_filling_ratio()
            _data_of_equipment['filling_ratio_in_percentage'] = equipment.get_filling_ratio_in_percentage()
            _data_of_equipment['tb'] = equipment.tb
            _data_of_equipment['project_folder'] = _folder
            data_of_equipments.append(_data_of_equipment)

        session['total_of_var'] = total_of_var

        return render_template('generation_preview.html', equipments=data_of_equipments, iterator=Integer(1))

    return render_template('project.html', form=form)


@app.route('/project/add', methods=['GET','POST'])
def project_add():
    if request.method == 'POST':
        project_data = session.get('data')
        project = Project(project_data['client'],
                          project_data['project_name'],
                          project_data['subproject_name'],
                          )
        post_add = project.add(project)
        project = lastProject()

        total_of_var = session.get('total_of_var')
        project_versioning = ProjectVersioning(1,
                                               project_data['excel_file'],
                                               project_data['template_file'],
                                               total_of_var['to_fill'],
                                               total_of_var['filled'],
                                               project
                                               )

        project_versioning = project_versioning.add(project_versioning)

        if not post_add and project_versioning:
            new_project_folder = os.path.join(app.config['UPLOAD_FOLDER'], project.id)
            move(session['project_folder'], new_project_folder)

            if project_data['subproject_name']:
                zf_name = "scripts-{0}-{1}-{2}.zip".format(project_data['client'], project_data['project_name'], project_data['subproject_name'])
            else:
                zf_name = "scripts-{0}-{1}.zip".format(project_data['client'], project_data['project_name'])

            try:
                zip_file(new_project_folder, os.path.join(new_project_folder, zf_name))
            except:
                pass
            else:
                return send_from_directory(new_project_folder, zf_name, as_attachment=True)

            return project_display_all()
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
    projects = Project.query.all()
    for p in projects:
        _all_version_of_the_project = p.version.all()
        if _all_version_of_the_project:
            last_version = _all_version_of_the_project[-1]
            for item in ('excelFile', 'templateFile'):
                setattr(p, item, getattr(last_version, item))

    return render_template('project_display_all.html', project=projects)

@app.route('/project/display/<id>', methods=['GET','POST'])
def project_display(id):
    project = Project.query.get(id)

    if project is None:
        flash("The project does not exist in the database")
        return redirect(url_for('project_display_all'))
    form = ProjectForm(request.form)
    return render_template('project_display.html', project=project, form=form, alert='None', message='')

@app.route('/project/upgrade/<id>', methods=['GET','POST'])
def project_upgrade(id):
    project = Project.query.get(id)
    project_folder = os.path.join(app.config['UPLOAD_FOLDER'], id)
    form = ProjectForm(request.form)
    if request.method == 'POST' and form.validate():

        excel_file = request.files['excel_file']
        excel_file_path = os.path.join(project_folder, secure_filename(excel_file.filename))
        excel_file.save(excel_file_path)

        template_file = request.files['template_file']
        template_file_path = os.path.join(project_folder, secure_filename(template_file.filename))
        template_file.save(template_file_path)

        project = dict()
        for item in ('client', 'project_name', 'subproject_name'):
            project[item] = request.form[item]
        for item, path in [('excel_file', excel_file.filename), ('template_file', template_file.filename)]:
            project[item] = path
        session['data'] = project
        try:
            equipments, wb, hostnames = nsg_processing(excel_file_path, template_file_path)
        except:
            exit()
            #TODO: Add a return page that handles this error

        session['hostnames'] = hostnames

        data_of_equipments = list()
        for equipment in equipments:
            equipment.save_script_as(project_folder, equipment.get_value_of_var('Hostname', wb))
            _data_of_equipment = dict()
            for item in ('Hostname', 'Equipment', 'Type'):
                _data_of_equipment[item] = equipment.get_value_of_var(item, wb)
            _data_of_equipment['filling_ratio'] = equipment.get_filling_ratio()
            _data_of_equipment['filling_ratio_in_percentage'] = equipment.get_filling_ratio_in_percentage()
            _data_of_equipment['tb'] = equipment.tb
            _data_of_equipment['project_folder'] = project_folder
            data_of_equipments.append(_data_of_equipment)


        return render_template('generation_preview.html', equipments=data_of_equipments, iterator=Integer(1))

    return render_template('project.html', form=form)


@app.route('/project/update/<id>', methods=['GET','POST'])
def project_update(id):
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

@app.route('/project/delete/<id>')
def project_delete(id):
    project = Project.query.get(id)
    if project == None:
        flash("This entry does not exist in the database")
        return redirect(url_for('user_display_all'))
    post_delete = project.delete(project)
    if not post_delete:
        flash("User was deleted successfully")
    else:
        error = post_delete
        flash(error)
    return redirect(url_for('project_display_all'))


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

@app.route('/download/<id>/<filename>')
def send_file_by_id_and_filename(id, filename):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], id)
    return send_from_directory(folder, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5005)
