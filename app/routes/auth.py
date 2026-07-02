from flask import Blueprint, render_template, request, redirect, session, flash
auth_bp = Blueprint('auth', __name__)
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        from app.models.user import authenticate
        if authenticate(username, password):
            session['user'] = username
            return redirect('/')
        flash('Invalid credentials', 'danger')
    return render_template('login.html')
@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')
@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    if 'user' not in session: return redirect('/login')
    old_pw = request.form.get('old_password', '')
    new_pw = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')
    if new_pw != confirm: flash('Passwords do not match', 'danger'); return redirect('/')
    if len(new_pw) < 6: flash('Password must be at least 6 characters', 'danger'); return redirect('/')
    from app.models.user import change_password
    if change_password(session['user'], old_pw, new_pw): flash('Password changed successfully', 'success')
    else: flash('Current password is incorrect', 'danger')
    return redirect('/')
