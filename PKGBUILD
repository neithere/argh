# Maintainer: Andrey Mikhaylenko <neithere at gmail dot com>
# Contributor: Fabien Devaux <fdev31 at gmail dot com>
pkgname=python2-argh
pkgver=0.14.2
pkgrel=1
pkgdesc="A simple argparse wrapper"
arch=(any)
url="http://bitbucket.org/neithere/argh/"
license=('LGPL3')
depends=('python2>=2.5' 'python2-argparse>=1.1')
makedepends=('python2-distribute')
provides=()
conflicts=()
replaces=()
backup=()
options=(!emptydirs)
install=
source=(http://pypi.python.org/packages/source/a/argh/argh-${pkgver}.tar.gz)
md5sums=('7711a0437cdaad18fcd600ee846d4939')

build() {
   cd "${srcdir}/argh-${pkgver}"
   python2 setup.py install --root="${pkgdir}" --optimize=1 || exit 1
}
