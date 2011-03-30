#!/usr/bin/perl
use strict;
use warnings;
use Config;
use IPC::Run3;
use CGI qw(:standard);
use File::Temp qw/ tempfile tempdir /;
use XML::Simple;
use Data::Dumper;
use Encode;
use utf8;
use HTML::TreeBuilder;
use Cwd;
use Carp;
$SIG{__DIE__}  = sub { Carp::confess(@_) };
$SIG{__WARN__} = sub { Carp::cluck(@_) };

#my $dir = getcwd;

#print "Content-type: text/html\n\n";
#print $dir;

my $tex = << 'TEX';
\documentclass[a5paper]{tbook}
%\\documentclass[a5paper, twocolumn]{tbook}
\usepackage[deluxe,multi]{otf}
%\\usepackage[expert, deluxe]{otf}
%##MyAUTHOR##
%\\usepackage{utf}
%\\usepackage{furikana}
%\\usepackage{type1cm}
%\\def\\rubykatuji{\\rubyfamily\\tiny}
%\\def\\rubykatuji{\\tiny}%for UTF package
%\\renewenvironment{teihon}{\\comment}{\\endcomment}

\usepackage[device=kindle2,size=large]{sensyo}
\title{hlhz}
\author{xh}
\date{}
\begin{document}
\setlength{\parindent}{2em}
%\includegraphics[angle=90, width=10cm, height=10cm]{hlhz/OEBPS/Images/Cover.png}
%\maketitle
%\tableofcontents
%\pagestyle{empty}
%\pagenumbering{gobble}
%\tchrm
%\large
%\bf
\input{a.txt}
\end{document}

TEX

my $text_encoding = "euc-jp";
my $plain_encoding = "sjis";
#umask 0666;
#umask 0750;

my $epub_url = param('epub') || "http://wp.1000ebooks.tw/wp-content/plugins/download-monitor/download.php?id=4";
my $zip_url = param('zip');
#print $epub_url;
#print $zip_url;

my $tempdir = tempdir( CLEANUP => 1 );
#my $tempdir = tempdir( CLEANUP => 0 );

my @cmd = ("wget", "-O$tempdir/a.epub", $epub_url);
#my @cmd = ("wget", "--trust-server-names", "-P$tempdir", $epub_url);
my ($in,$out,$err);
#$ENV{http_proxy} = "http://10.113.2.156:3128";
run3 \@cmd, undef, \$out, \$err;
#print "out: $out";
#print "err: $err";

@cmd = ("7za", "x", "-o$tempdir/content", "$tempdir/a.epub");
run3 \@cmd, undef, \$out, \$err;
#print "in: $in";
#print "out: $out";
#print "err: $err";

my $ref = XMLin("$tempdir/content/OEBPS/toc.ncx");
my $navpoint = $ref->{navMap}{navPoint};
my @order = sort {$navpoint->{$a}{playOrder} <=> $navpoint->{$b}{playOrder}} (keys %{$navpoint});
my @content_files = map { "$tempdir/content/OEBPS/".$navpoint->{$_}{content}{src} } @order;
my $outbuf = "";
for my $file (@content_files) {
#    print $file,$/;
    my $tree = HTML::TreeBuilder->new; # empty tree
    $tree->parse_file($file);
#    $tree->dump;
    my %content = map {
        $_ => [$tree->look_down( '_tag' , $_ )];
    } qw(title h1 h2 p);
    #    print Dumper(\%content);
    #    for my $tag qw(title h1 h2 h3) {
    $outbuf .= output("\\chapter{".
                     decode('utf8',$content{title}[0]->as_text)
                         ."}").$/;
    for my $item (@{$content{p}}) {
        $outbuf .= output(decode('utf8', $item->as_text));
        #            print $item->as_text;
        $outbuf .= "$/$/";
    }
#        print $tag, ":", map { defined $_ && ref $_ eq 'HASH' && $_->as_text } @{$content{$tag}}, $/;
    $tree = $tree->delete;
}

my $fho;
open $fho, ">:raw", "$tempdir/a.txt" or die "$!";
print $fho $outbuf;
close $fho;

open $fho, ">:utf8", "$tempdir/a.tex" or die "$!";
print $fho $tex;
close $fho;

#chdir $tempdir;
@cmd = ("cp", "/home/ubuntu/sensyo.sty", $tempdir);
run3 \@cmd, undef, \$out, \$err;
#print "in: $in";x
#print "out: $out";
#print "err: $err";

$ENV{TEXINPUTS} = ".:/home/ubuntu/.texmf-var/tex/otf:";
$ENV{TEXFONTS} =  ".:/home/ubuntu/.texmf-var/fonts//:";
@cmd = ("platex", "-output-directory", $tempdir, "$tempdir/a.tex");
run3 \@cmd, undef, \$out, \$err;
#print "in: $in";
#print "out: $out";
#print "err: $err";

#$ENV{TEXFONTS} =  ".:/usr/share/fonts/truetype//:/home/ubuntu/.fonts:/home/ubuntu/.texmf-var/fonts//:";
@cmd = ("dvipdfmx", "-vv", "-z", "9", "-f","/home/ubuntu/cid-x.map", "-o", "$tempdir/a.pdf", "$tempdir/a.dvi");
run3 \@cmd, undef, \$out, \$err;
#print "in: $in";
#print "out: $out";
my $pdf_file="$tempdir/a.pdf";
print("err: $err"),exit 1 unless -r $pdf_file;
#print("err: $err"),exit 1;

my $fh;
open $fh, "<:raw", $pdf_file or die $!;
my $pdf_content = do { local $/; <$fh> };
print "Content-Type:application/x-download\n";   
print "Content-Disposition:attachment;filename=$pdf_file\n\n";  
binmode STDOUT, ':raw';
print $pdf_content;


sub output {
    my $plain_text = shift;
    return
        encode($text_encoding, decode($plain_encoding,
                                      encode(
                                          $plain_encoding,
                                          $plain_text,
                                          #			Encode::FB_PERLQQ
                                          sub { sprintf "\\UTF{%X}",$_[0]	}
                                      )
                                  ));
}



__END__


__END__

foreach my $key (sort keys(%ENV)) {
#  print "$key = $ENV{$key}<p>";
}
foreach my $key (sort keys(%Config)) {
  print "$key = $Config{$key}<p>" if defined $Config{$key};
}
#!/home/yj/perl5/perlbrew/perls/current/bin/perl5.12.3
