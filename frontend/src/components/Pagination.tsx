type Props = {
  skip: number
  limit: number
  total: number
  onChange: (skip: number) => void
}

function Pagination({ skip, limit, total, onChange }: Props) {
  // Všetko sa zmestí na jednu stranu -> tlačidlá netreba.
  if (total <= limit) return null

  const currentPage = Math.floor(skip / limit) + 1
  const pageCount = Math.ceil(total / limit)

  return (
    <div className="pagination">
      <button className="secondary" disabled={currentPage === 1} onClick={() => onChange(skip - limit)}>
        Predchádzajúca
      </button>
      <span>
        Strana {currentPage} z {pageCount}
      </span>
      <button className="secondary" disabled={currentPage === pageCount} onClick={() => onChange(skip + limit)}>
        Ďalšia
      </button>
    </div>
  )
}

export default Pagination
