use 5.006;
use strict;
use warnings;
use ExtUtils::MakeMaker;

WriteMakefile(
    NAME                => 'Text::sensyo4kindle',
    AUTHOR              => q{Liyuray Li <liyuray@gmail.com>},
    VERSION_FROM        => 'lib/Text/sensyo4kindle.pm',
    ABSTRACT_FROM       => 'lib/Text/sensyo4kindle.pm',
    ($ExtUtils::MakeMaker::VERSION >= 6.3002
      ? ('LICENSE'=> 'perl')
      : ()),
    PL_FILES            => {},
    PREREQ_PM => {
        'Test::More' => 0,
    },
    dist                => { COMPRESS => 'gzip -9f', SUFFIX => 'gz', },
    clean               => { FILES => 'Text-sensyo4kindle-*' },
);
