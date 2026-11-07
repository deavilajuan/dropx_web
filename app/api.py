from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app import db, jwt
from app.models import STATUSES, Package, PackageEvent, User

# Todas las rutas de este archivo empiezan con /api
bp = Blueprint('api', __name__, url_prefix='/api')


# ---------- Autenticación ----------
@bp.post('/auth/login')
def login():
    """Inicia sesión (admin, manager o courier) y devuelve el token JWT."""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify(message='El correo y la contraseña son obligatorios'), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify(message='Correo o contraseña incorrectos'), 401

    # En el token se guarda el id (como texto) y el rol
    token = create_access_token(identity=str(user.id), additional_claims={'role': user.role})
    return jsonify(token=token, user=user.to_dict())


@bp.get('/auth/me')
@jwt_required()
def me():
    """Devuelve el usuario dueño del token."""
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify(message='Usuario no encontrado'), 404
    return jsonify(user=user.to_dict())


# ---------- Paquetes del repartidor ----------
@bp.get('/packages')
@jwt_required()
def packages():
    """Lista los paquetes asignados al repartidor del token (opcional: ?status=pending)."""
    query = Package.query.filter_by(courier_id=int(get_jwt_identity()))

    status = request.args.get('status')
    if status:
        if status not in STATUSES:
            return jsonify(message='El estado no es válido'), 400
        query = query.filter_by(status=status)

    items = query.order_by(Package.is_urgent.desc(), Package.id.desc()).all()
    return jsonify(packages=[item.to_dict() for item in items])


@bp.get('/packages/<int:package_id>')
@jwt_required()
def package_detail(package_id):
    """Devuelve un paquete, solo si está asignado al repartidor del token."""
    item = Package.query.filter_by(id=package_id, courier_id=int(get_jwt_identity())).first()
    if not item:
        return jsonify(message='Paquete no encontrado'), 404
    return jsonify(package=item.to_dict())


# Cambios de estado que puede hacer el repartidor: {estado actual: [estados permitidos]}
TRANSITIONS = {
    'pending': ['picked_up', 'issue'],
    'picked_up': ['delivered', 'issue'],
    'issue': ['picked_up'],
    'delivered': [],
}


@bp.patch('/packages/<int:package_id>/status')
@jwt_required()
def change_status(package_id):
    """Cambia el estado de un paquete asignado al repartidor del token."""
    courier = db.session.get(User, int(get_jwt_identity()))
    item = Package.query.filter_by(id=package_id, courier_id=courier.id).first()
    if not item:
        return jsonify(message='Paquete no encontrado'), 404

    status = (request.get_json(silent=True) or {}).get('status')
    if status not in STATUSES:
        return jsonify(message='El estado no es válido'), 400
    if status not in TRANSITIONS[item.status]:
        return jsonify(message=f'No se puede pasar de "{STATUSES[item.status]}" a "{STATUSES[status]}"'), 409

    item.status = status
    item.delivered_at = datetime.now() if status == 'delivered' else None
    item.events.append(PackageEvent(title=STATUSES[status], description=f'Actualizado por {courier.name}.'))
    db.session.commit()
    return jsonify(package=item.to_dict())


# TO DO: Habilitar CORS (flask-cors) si la app Flutter se prueba en Chrome.


# ---------- Mensajes de error del token (en español) ----------
@jwt.unauthorized_loader
def missing_token(reason):
    return jsonify(message='Falta el token de acceso'), 401


@jwt.invalid_token_loader
def invalid_token(reason):
    return jsonify(message='El token no es válido'), 401


@jwt.expired_token_loader
def expired_token(header, payload):
    return jsonify(message='El token expiró, inicia sesión de nuevo'), 401
