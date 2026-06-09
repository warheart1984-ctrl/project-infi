/*
 * Nova NorthStar CoG OS gatekeeper — custom PID 1.
 * Mounts essential filesystems, logs startup, execs /etc/rc.sh.
 */
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/reboot.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/reboot.h>
#include <sys/stat.h>
#include <unistd.h>

static void setup_mounts(void) {
    mkdir("/proc", 0555);
    mkdir("/sys", 0555);
    mkdir("/dev", 0755);
    mount("proc", "/proc", "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL);
    mount("sysfs", "/sys", "sysfs", MS_NOSUID | MS_NODEV | MS_NOEXEC, NULL);
    mount("devtmpfs", "/dev", "devtmpfs", MS_NOSUID | MS_STRICTATIME, NULL);
    mkdir("/dev/pts", 0755);
    mount("devpts", "/dev/pts", "devpts", MS_NOSUID | MS_NOEXEC, "newinstance,ptmxmode=0666,mode=0620,gid=5");
    mkdir("/run", 0755);
    mount("tmpfs", "/run", "tmpfs", MS_NOSUID | MS_NODEV, "mode=0755");
}

static void redirect_stdio(void) {
    mkdir("/var/log/cog", 0755);
    int fd = open("/var/log/cog/pid1.log", O_WRONLY | O_CREAT | O_APPEND, 0644);
    if (fd >= 0) {
        dup2(fd, STDOUT_FILENO);
        dup2(fd, STDERR_FILENO);
        if (fd > STDERR_FILENO) {
            close(fd);
        }
    }
}

int main(void) {
    signal(SIGCHLD, SIG_IGN);
    signal(SIGHUP, SIG_IGN);
    setsid();
    redirect_stdio();
    setup_mounts();
    fprintf(stderr, "Nova NorthStar CoG OS gatekeeper PID1 starting\n");
    fflush(stderr);
    execl("/etc/rc.sh", "rc.sh", (char *)NULL);
    fprintf(stderr, "failed to exec /etc/rc.sh: %s\n", strerror(errno));
    reboot(RB_AUTOBOOT);
    return 1;
}
