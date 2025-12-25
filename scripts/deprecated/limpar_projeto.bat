@echo off
:: Script de Limpeza Automática - ISP Monitor
:: Remove arquivos obsoletos e organiza o projeto

echo ========================================
echo LIMPEZA DO PROJETO ISP MONITOR
echo ========================================
echo.

:: Criar diretório de backup
echo [1/6] Criando backup de seguranca...
if not exist "backup_limpeza" mkdir backup_limpeza

:: Backup arquivos SQLite
if exist "monitor.db" copy "monitor.db" "backup_limpeza\" >nul 2>&1
if exist "monitor.db-shm" copy "monitor.db-shm" "backup_limpeza\" >nul 2>&1
if exist "monitor.db-wal" copy "monitor.db-wal" "backup_limpeza\" >nul 2>&1
if exist "*.old" copy "*.old" "backup_limpeza\" >nul 2>&1
if exist "*.OLD" copy "*.OLD" "backup_limpeza\" >nul 2>&1

echo    Backup criado em: backup_limpeza\
echo.

:: Remover arquivos SQLite obsoletos
echo [2/6] Removendo arquivos SQLite obsoletos...
if exist "monitor.db" del /q "monitor.db"
if exist "monitor.db-shm" del /q "monitor.db-shm"
if exist "monitor.db-wal" del /q "monitor.db-wal"
if exist "monitor.db-shm.old" del /q "monitor.db-shm.old"
if exist "monitor.db-wal.old" del /q "monitor.db-wal.old"
if exist "monitor.db.old" del /q "monitor.db.old"
if exist "migrate_db.py.OLD" del /q "migrate_db.py.OLD"
echo    SQLite files removidos
echo.

:: Remover scripts/GUI não usados
echo [3/6] Removendo scripts e GUI nao usados...
if exist "launcher.pyw" del /q "launcher.pyw"
if exist "setup_gui.py" del /q "setup_gui.py"
if exist "repair.ps1" del /q "repair.ps1"
if exist "iniciar_sistema.bat" del /q "iniciar_sistema.bat"
if exist "backend\diagnose_firewall.ps1" del /q "backend\diagnose_firewall.ps1"
echo    Scripts obsoletos removidos
echo.

:: Arquivar scripts de migração
echo [4/6] Arquivando scripts de migracao...
if not exist "scripts\archive" mkdir "scripts\archive"
if exist "scripts\init_postgres.py" move "scripts\init_postgres.py" "scripts\archive\" >nul 2>&1
if exist "scripts\migrar_sqlite_para_postgres.py" move "scripts\migrar_sqlite_para_postgres.py" "scripts\archive\" >nul 2>&1
echo    Scripts arquivados em: scripts\archive\
echo.

:: Arquivar ferramentas de migração
echo [5/6] Arquivando ferramentas de migracao...
if not exist "backend\tools\archive" mkdir "backend\tools\archive"
move "backend\tools\add_*.py" "backend\tools\archive\" >nul 2>&1
move "backend\tools\update_*.py" "backend\tools\archive\" >nul 2>&1
move "backend\tools\disable_*.py" "backend\tools\archive\" >nul 2>&1
move "backend\tools\force_*.py" "backend\tools\archive\" >nul 2>&1
echo    Ferramentas arquivadas em: backend\tools\archive\
echo.

:: Remover venv duplicado
echo [6/6] Removendo venv duplicado...
if exist "venv" (
    echo    Removendo venv\ ...
    rmdir /s /q "venv" 2>nul
    echo    venv\ removido
) else (
    echo    venv\ nao encontrado (OK)
)
echo.

echo ========================================
echo LIMPEZA CONCLUIDA!
echo ========================================
echo.
echo Arquivos removidos:
echo   - SQLite databases (obsoletos)
echo   - Scripts de migracao (arquivados)
echo   - GUI nao usada (removida)
echo   - venv duplicado (removido)
echo.
echo Backup criado em: backup_limpeza\
echo.
echo Projeto organizado e limpo!
echo.
pause
