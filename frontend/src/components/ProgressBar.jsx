const ProgressBar = ({ current, total, percent }) => {
    return (
      <div className="w-full my-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Progress: {current} / {total}</span>
          <span>{percent}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-blue-500 h-3 rounded-full transition-all duration-300"
            style={{ width: `${percent}%` }}
          ></div>
        </div>
      </div>
    )
  }

export default ProgressBar