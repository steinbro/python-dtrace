#!/usr/sbin/dtrace -s

#pragma D option quiet

::hello:
{
printf("%s:%s:%s:%s %s\n", probeprov, probemod, probefunc, probename, copyinstr(arg0));
}
::hello:int
{
printf("Int test:%d\n", arg1);
}
::hello:name
{
exit(0);
}
