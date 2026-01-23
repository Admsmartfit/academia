# app/utils/backup.py

import shutil
from datetime import datetime
from pathlib import Path


def backup_database() -> bool:
    """
    Cria backup do banco de dados SQLite.

    O backup e salvo na pasta 'backups/' com timestamp.
    Mantem apenas os 7 backups mais recentes.

    Returns:
        True se o backup foi criado com sucesso
    """
    db_path = Path('instance/academia.db')
    backup_dir = Path('backups')

    # Verificar se o banco existe
    if not db_path.exists():
        print(f"[BACKUP] Banco de dados nao encontrado: {db_path}")
        return False

    # Criar diretorio de backups se nao existir
    backup_dir.mkdir(exist_ok=True)

    # Gerar nome do arquivo com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'academia_backup_{timestamp}.db'
    backup_path = backup_dir / backup_name

    try:
        # Copiar banco de dados
        shutil.copy2(db_path, backup_path)
        print(f"[BACKUP] Criado: {backup_path}")

        # Manter apenas os 7 backups mais recentes
        cleanup_old_backups(backup_dir, keep=7)

        return True

    except Exception as e:
        print(f"[BACKUP] Erro ao criar backup: {e}")
        return False


def cleanup_old_backups(backup_dir: Path, keep: int = 7) -> int:
    """
    Remove backups antigos, mantendo apenas os mais recentes.

    Args:
        backup_dir: Diretorio de backups
        keep: Quantidade de backups a manter

    Returns:
        Quantidade de backups removidos
    """
    backups = sorted(backup_dir.glob('academia_backup_*.db'))
    removed_count = 0

    # Remover os mais antigos (manter os ultimos 'keep')
    for old_backup in backups[:-keep]:
        try:
            old_backup.unlink()
            print(f"[BACKUP] Removido: {old_backup.name}")
            removed_count += 1
        except Exception as e:
            print(f"[BACKUP] Erro ao remover {old_backup.name}: {e}")

    return removed_count


def restore_database(backup_filename: str) -> bool:
    """
    Restaura o banco de dados a partir de um backup.

    Antes de restaurar, cria um backup de emergencia do banco atual.

    Args:
        backup_filename: Nome do arquivo de backup (ex: academia_backup_20240101_120000.db)

    Returns:
        True se a restauracao foi bem sucedida

    Raises:
        FileNotFoundError: Se o backup nao for encontrado
    """
    backup_path = Path('backups') / backup_filename
    db_path = Path('instance/academia.db')

    # Verificar se o backup existe
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup nao encontrado: {backup_filename}")

    try:
        # Criar backup de emergencia do banco atual (se existir)
        if db_path.exists():
            emergency_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            emergency_path = Path(f'instance/academia_emergency_{emergency_timestamp}.db')
            shutil.copy2(db_path, emergency_path)
            print(f"[BACKUP] Backup de emergencia criado: {emergency_path}")

        # Restaurar backup
        shutil.copy2(backup_path, db_path)
        print(f"[BACKUP] Banco restaurado de: {backup_filename}")

        return True

    except Exception as e:
        print(f"[BACKUP] Erro ao restaurar: {e}")
        raise


def list_backups() -> list:
    """
    Lista todos os backups disponiveis.

    Returns:
        Lista de dicionarios com informacoes dos backups
    """
    backup_dir = Path('backups')

    if not backup_dir.exists():
        return []

    backups = []
    for backup_file in sorted(backup_dir.glob('academia_backup_*.db'), reverse=True):
        stat = backup_file.stat()
        backups.append({
            'filename': backup_file.name,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'created_at': datetime.fromtimestamp(stat.st_mtime)
        })

    return backups
