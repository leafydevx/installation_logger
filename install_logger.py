#!/usr/bin/env python3
"""
Installation Logger v3.0
Tracks all package installations with status levels and security alerts
Author: David (@leafytosh)
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class InstallLogger:
    def __init__(self):
        self.log_dir = f"{os.path.expanduser('~')}/.install_logger"
        self.log_file = f"{self.log_dir}/install_log.json"
        self.report_file = f"{self.log_dir}/install_report.txt"
        Path(self.log_dir).mkdir(exist_ok=True)
        
        # Load existing logs
        self.logs = self.load_logs()
        
        # Dangerous packages to watch
        self.dangerous = ['rm', 'dd', 'format', 'fdisk']
        self.deprecated = ['python2', 'python2-pip']
        
    def load_logs(self):
        """Load existing logs"""
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_logs(self):
        """Save logs to file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.logs, f, indent=2)
    
    def get_package_info(self, package):
        """Get package info"""
        try:
            result = subprocess.run(['pacman', '-Si', package], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                info = {}
                for line in result.stdout.split('\n'):
                    if ':' in line:
                        key, val = line.split(':', 1)
                        info[key.strip()] = val.strip()
                return info
        except:
            pass
        return {}
    
    def check_dependencies(self, package):
        """Check for dependency issues"""
        issues = []
        try:
            result = subprocess.run(['pacman', '-Si', package],
                                  capture_output=True, text=True, timeout=5)
            if 'Dependency' in result.stdout:
                deps = [line for line in result.stdout.split('\n') if 'Depend' in line]
                if deps:
                    for dep in deps:
                        if 'deprecated' in dep.lower():
                            issues.append(f"Deprecated dependency: {dep}")
        except:
            pass
        return issues
    
    def determine_status(self, package, info, deps):
        """Determine install status"""
        # CATASTROPHIC
        if any(danger in package.lower() for danger in self.dangerous):
            return "CATASTROPHIC", "Dangerous system tool - extreme caution"
        
        if deps and len(deps) > 5:
            return "CATASTROPHIC", "Too many dependencies - potential conflicts"
        
        # OK
        if any(dep in package.lower() for dep in self.deprecated):
            return "OK", "Deprecated package - consider alternatives"
        
        if 'Old Version' in info.get('Version', ''):
            return "OK", "Outdated version available"
        
        # GOOD
        return "GOOD", "Installation clean - no issues detected"
    
    def log_installation(self, package):
        """Log a package installation"""
        print(f"\n{Colors.CYAN}[*] Analyzing {package}...{Colors.END}\n")
        
        info = self.get_package_info(package)
        deps = self.check_dependencies(package)
        status, reason = self.determine_status(package, info, deps)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "package": package,
            "version": info.get('Version', 'unknown'),
            "status": status,
            "reason": reason,
            "dependencies": len(deps),
            "issues": deps
        }
        
        self.logs.append(log_entry)
        self.save_logs()
        
        # Print status
        if status == "GOOD":
            print(f"{Colors.GREEN}[✓ GOOD]{Colors.END} {package}")
            print(f"   {Colors.GREEN}No worries - clean installation{Colors.END}\n")
        
        elif status == "OK":
            print(f"{Colors.YELLOW}[~ OK]{Colors.END} {package}")
            print(f"   {Colors.YELLOW}⚠️  {reason}{Colors.END}\n")
        
        elif status == "CATASTROPHIC":
            print(f"{Colors.RED}[✗ CATASTROPHIC]{Colors.END} {package}")
            print(f"   {Colors.RED}🚨 {reason}{Colors.END}")
            print(f"   {Colors.RED}YOU NEED TO FIX THIS NOW{Colors.END}\n")
        
        return log_entry
    
    def generate_report(self):
        """Generate installation report"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}GENERATING REPORT...{Colors.END}\n")
        
        good = len([l for l in self.logs if l['status'] == 'GOOD'])
        ok = len([l for l in self.logs if l['status'] == 'OK'])
        catastrophic = len([l for l in self.logs if l['status'] == 'CATASTROPHIC'])
        
        report = f"""
╔════════════════════════════════════════════════════╗
║          INSTALLATION LOGGER REPORT v3.0           ║
╚════════════════════════════════════════════════════╝

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUMMARY
═══════════════════════════════════════════════════
✓ GOOD:           {good} packages
~ OK:             {ok} packages  
✗ CATASTROPHIC:   {catastrophic} packages

TOTAL INSTALLATIONS: {len(self.logs)}

DETAILED LOG
═══════════════════════════════════════════════════
"""
        
        for log in self.logs:
            report += f"\n[{log['timestamp']}]\n"
            report += f"  Package:     {log['package']}\n"
            report += f"  Version:     {log['version']}\n"
            report += f"  Status:      {log['status']}\n"
            report += f"  Reason:      {log['reason']}\n"
            if log['issues']:
                report += f"  Issues:      {', '.join(log['issues'][:2])}\n"
            report += "\n"
        
        # Recommendations
        report += "\nRECOMMENDATIONS\n"
        report += "═══════════════════════════════════════════════════\n"
        
        if catastrophic > 0:
            report += f"\n🚨 {catastrophic} CATASTROPHIC issues found!\n"
            for log in self.logs:
                if log['status'] == 'CATASTROPHIC':
                    report += f"   - Review: {log['package']}\n"
        
        if ok > 0:
            report += f"\n⚠️  {ok} packages need attention\n"
            for log in self.logs:
                if log['status'] == 'OK':
                    report += f"   - Consider: {log['package']}\n"
        
        report += f"\n✓ {good} packages are clean\n"
        
        # Save report
        with open(self.report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n{Colors.CYAN}Report saved: {self.report_file}{Colors.END}\n")
    
    def live_monitor(self):
        """Monitor installations in real-time"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}INSTALLATION LOGGER v3.0 - LIVE MONITOR{Colors.END}")
        print(f"{Colors.CYAN}Watching for package installations...{Colors.END}\n")
        print(f"Usage:")
        print(f"  {Colors.BOLD}sudo pacman -S package{Colors.END}  (install normally)")
        print(f"  {Colors.BOLD}logger{Colors.END}                    (to show this menu)\n")
        
        while True:
            try:
                choice = input(f"{Colors.CYAN}Enter package name to log (or 'report'/'exit'): {Colors.END}").strip()
                
                if choice.lower() == 'exit':
                    print(f"{Colors.GREEN}Goodbye!{Colors.END}\n")
                    break
                elif choice.lower() == 'report':
                    self.generate_report()
                elif choice:
                    self.log_installation(choice)
            
            except KeyboardInterrupt:
                print(f"\n{Colors.GREEN}Exiting...{Colors.END}\n")
                break

# =====================================================================
# QUICK INSTALL LOGGER (for monitoring live installations)
# =====================================================================

def monitor_pacman_install():
    """Monitor pacman installations in real-time"""
    logger = InstallLogger()
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}╔════════════════════════════════════════════════╗{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}║   INSTALLATION LOGGER v3.0 - LIVE MODE        ║{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}║   By leafy (@leafytosh)                        ║{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}╚════════════════════════════════════════════════╝{Colors.END}\n")
    
    # Get recently installed packages
    try:
        result = subprocess.run(['pacman', '-Q'], capture_output=True, text=True)
        packages = [line.split()[0] for line in result.stdout.strip().split('\n')[-5:]]
        
        print(f"{Colors.YELLOW}Recent installations detected:{Colors.END}\n")
        
        for i, pkg in enumerate(packages, 1):
            logger.log_installation(pkg)
            time.sleep(0.5)
        
        logger.generate_report()
        
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'monitor':
        logger = InstallLogger()
        logger.live_monitor()
    else:
        monitor_pacman_install()